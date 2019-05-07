# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                 Python class for EDXML data stream generation
#
#                  Copyright (c) 2010 - 2016 by D.H.J. Takken
#                          (d.h.j.takken@xs4all.nl)
#
#          This file is part of the EDXML Software Development Kit (SDK).
#
#
#  The EDXML SDK is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  The EDXML SDK is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with the EDXML SDK.  If not, see <http://www.gnu.org/licenses/>.
#
#
#  ===========================================================================
#
#

"""EDXMLWriter

This module contains the EDXMLWriter class, which is used
to generate EDXML streams.

"""
from collections import deque
import sys

import edxml

from lxml import etree
from copy import deepcopy
from EDXMLBase import EDXMLBase, EvilCharacterFilter, EDXMLValidationError


class EDXMLWriter(EDXMLBase, EvilCharacterFilter):
    """
    Class for generating EDXML streams

    The Output parameter is a file-like object that will be used to send the XML data to.
    This file-like object can be pretty much anything, as long as it has a write() method
    and a mode containing 'a' (opened for appending). When the Output parameter is omitted,
    the generated XML data will be returned by the methods that generate output.

    The optional Validate parameter controls if the generated EDXML stream should be auto-validated
    or not. Automatic validation is enabled by default.

    Args:
        output (file, optional): File-like output object
        validate (bool, optional): Enable output validation (True) or not (False)
        log_repaired_events (bool, optional): Log repaired events (True) or not (False)
    """

    class OutputBuffer(object):
        """
        A buffer for collecting the output of the lxml xml writer.
        """

        def __init__(self):
            self.buffer = deque()

            self.mode = 'a'

        def write(self, data):
            # For some reason, lxml write regular strings rather than
            # unicode strings. We need to tell Python that it is
            # actually unicode data.
            self.buffer.append(unicode(data, encoding='utf-8'))

    def __init__(self, output=None, validate=True, log_repaired_events=False):

        super(EDXMLWriter, self).__init__()

        self.__ontology = None
        self.__schema = None                 # type: etree.RelaxNG
        self.__event_type_schema_cache = {}     # type: Dict[str, etree.RelaxNG]
        self.__event_type_schema = None        # type: etree.RelaxNG
        self.__just_wrote_ontology = False
        self.__log_repaired_events = log_repaired_events
        self.__invalid_event_count = 0
        self.__validate = validate
        self.__output = output
        self.__element_stack = []
        self.__current_event_type_name = None
        self.__current_event_source_uri = None
        self.__event_group_xml_writer = None

        self.__num_events_repaired = 0
        self.__num_events_produced = 0

        if self.__output is None:
            # Create an output buffer to capture XML data
            self.__output = self.OutputBuffer()

        # Passing a file name as output will make lxml open the file, and it will open it with mode 'w'. Since
        # we use multiple lxml file writers to produce output, the output will be truncated mid stream. Therefore,
        # we only accept files and file-like objects as output, allowing us to verify if we can append to the file.
        if not hasattr(self.__output, 'write'):
            raise IOError(
                'The output of the EDXML writer does not look like an open file: ' + repr(self.__output))

        # If the output is not opened for appending,
        # we raise an error for the reason outlined above.
        if 'a' not in self.__output.mode:
            if self.__output == sys.stdout:
                # Unless the output is standard output, which cannot
                # be truncated. We make this exception because sys.stdout
                # object has mode 'w', which would normally qualify as unsafe.
                pass
            else:
                raise IOError(
                    'The mode attribute of the output of the EDXML writer must contain "a" (opened for appending).')

        # Initialize lxml.etree based XML generators. This
        # will write the XML declaration and open the
        # <events> tag.
        # Note that we use two XML generators. Due to the way
        # coroutines work, we can only flush the output buffer
        # after generating sub-elements of the <events> element
        # which contains the entire EDXML stream. That means we
        # need to build <eventgroup> tags in memory, which is
        # not acceptable. We solve that issue by writing the event
        # groups into a secondary XML generator, allowing us to
        # flush after each event.
        self.__writer = self.__outer_xml_serializer_coroutine()
        self.__writer.next()

        self.__current_element_type = ""
        self.__event_types = {}
        self.__object_types = {}

    def get_output(self):
        return self.__output

    def get_event_type_schema(self, event_type_name):
        if event_type_name not in self.__event_type_schema_cache:
            self.__event_type_schema_cache[event_type_name] = etree.RelaxNG(
                self.__ontology.get_event_type(event_type_name).generate_relax_ng(self.__ontology)
            )
        return self.__event_type_schema_cache.get(event_type_name)

    def __generate_event_validation_exception(self, event, event_element):
        try:
            self.__ontology.get_event_type(self.__current_event_type_name).validate_event_structure(event)

            # EventType structure checks out alright. Let us check the object values.
            self.__ontology.get_event_type(self.__current_event_type_name).validate_event_objects(event)

            # EventType validation did not find the issue. We have
            # no other option than to raise a RelaxNG validation error.
            raise EDXMLValidationError(
                "At xpath location %s: %s" %
                (
                    self.__event_type_schema.error_log.last_error.path,
                    self.__event_type_schema.error_log.last_error.message
                )
            )

        except EDXMLValidationError as exception:
            self.__invalid_event_count += 1
            raise EDXMLValidationError('An invalid event was produced:\n%s\n\nThe EDXML validator said: %s\n\n%s' % (
                etree.tostring(event_element, pretty_print=True).encode(
                    'utf-8'), exception,
                'Note that this exception is not fatal. You can recover by catching the EDXMLValidationError '
                'and begin writing a new event.'), sys.exc_info()[2])

    def __outer_xml_serializer_coroutine(self):
        """Coroutine which performs the actual XML serialisation"""
        with etree.xmlfile(self.__output, encoding='utf-8') as writer:
            if 'flush' not in dir(writer):
                raise Exception(
                    'The installed version of lxml is too old. Please install version >= 3.4.')
            writer.write_declaration()
            with writer.element('edxml', version='3.0.0'):
                writer.flush()
                try:
                    while True:
                        # This is the main loop which generates eventgroups elements.
                        element = (yield)
                        if element is None:
                            # Sending None signals the end of the generation of
                            # the ontology element, and the beginning of the
                            # eventgroups element.
                            with writer.element('eventgroups'):
                                writer.flush()
                                while True:
                                    element = (yield)
                                    if element is None:
                                        # Sending None signals the end of the generation of
                                        # the eventgroups element. We break out of the loop,
                                        # causing the context manager to write the closing
                                        # tag of the eventgroups element. We then fall back
                                        # into the outer while loop.
                                        break
                                    writer.write(element, pretty_print=True)
                                    writer.flush()
                        else:
                            writer.write(element, pretty_print=True)
                            writer.flush()
                except GeneratorExit:
                    pass

    def __inner_xml_serializer_coroutine(self, event_type_name, event_source_uri):
        """Coroutine which performs the actual XML serialisation of eventgroups"""
        with etree.xmlfile(self.__output, encoding='utf-8') as writer:
            with writer.element('eventgroup', **{'event-type': event_type_name, 'source-uri': event_source_uri}):
                writer.flush()
                try:
                    while True:
                        element = (yield)
                        writer.write(element, pretty_print=True)
                        writer.flush()
                except GeneratorExit:
                    pass

    def add_ontology(self, ontology):
        """

        Writes an EDXML ontology element into the output. This method
        may be called at any point in the EDXML generation process, it
        will automatically close and reopen the current eventgroup and
        eventgroups elements if necessary.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          ontology (edxml.ontology.Ontology): The ontology

        Returns:
          unicode: Generated output XML data

        """
        reopen_event_groups = False
        prev_event_type_name = None
        prev_event_source = None

        if len(self.__element_stack) > 0:
            if self.__element_stack[-1] == 'eventgroup':
                prev_event_type_name = self.__current_event_type_name
                prev_event_source = self.__current_event_source_uri
                self.close_event_group()

        if len(self.__element_stack) > 0:
            if self.__element_stack[-1] == 'eventgroups':
                reopen_event_groups = True
                self.close_event_groups()

        if self.__ontology is None:
            self.__ontology = ontology.validate()
        else:
            # We update our existing ontology, to make sure
            # that both are compatible.
            self.__ontology.update(ontology)

        try:
            self.__writer.send(ontology.generate_xml())
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.__event_type_schema_cache = {}
        self.__just_wrote_ontology = True

        if reopen_event_groups:
            self.open_event_groups()
        if prev_event_type_name is not None and prev_event_source is not None:
            self.open_event_group(prev_event_type_name, prev_event_source)

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def open_event_groups(self):
        """
        Opens the <eventgroups> element, containing all eventgroups

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        if len(self.__element_stack) > 0:
            self.error(
                'An <eventgroups> tag must be child of the <events> tag. Did you forget to call CloseDefinitions()?')

        if not self.__just_wrote_ontology:
            self.error(
                'Attempt to output an eventgroups element without a preceding ontology element.')
        self.__just_wrote_ontology = False

        # We send None to the outer XML generator, to
        # hint it that the ontology element has been
        # completed and we want it to generate the
        # eventgroups opening tag.
        try:
            self.__writer.send(None)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.__element_stack.append('eventgroups')

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def open_event_group(self, event_type_name, source_uri):
        """
        Opens an event group.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          event_type_name (str): Name of the eventtype
          source_uri (str): EDXML event source URI

        Returns:
          unicode: Generated output XML data

        """

        if len(self.__element_stack) == 0:
            self.open_event_groups()
        self.__element_stack.append('eventgroup')

        if self.__ontology.get_event_type(event_type_name) is None:
            raise EDXMLValidationError(
                'Attempt to open an event group using unknown event type: "%s"' % event_type_name)
        if self.__ontology.get_event_source(source_uri) is None:
            raise EDXMLValidationError(
                'Attempt to open an event group using unknown source URI: "%s"' % source_uri)

        self.__current_event_type_name = event_type_name
        self.__current_event_source_uri = source_uri

        if self.__validate:
            self.__event_type_schema = self.get_event_type_schema(
                self.__current_event_type_name)

        self.__event_group_xml_writer = self.__inner_xml_serializer_coroutine(
            self.__current_event_type_name, source_uri)
        self.__event_group_xml_writer.next()

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def close(self):
        """

        Finalizes the output data stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        if self.__just_wrote_ontology:
            # EDXML data streams must contain sequences of pairs of
            # an <ontology> element followed by an <eventgroups>
            # element. Apparently, we just wrote an <ontology>
            # element, so we must open a new eventgroups tag.
            self.open_event_groups()
        if len(self.__element_stack) > 0 and self.__element_stack[-1] == 'eventgroup':
            self.close_event_group()
        if len(self.__element_stack) > 0 and self.__element_stack[-1] == 'eventgroups':
            self.close_event_groups()
        self.__writer.close()

        if self.__num_events_produced > 0 and (100 * self.__num_events_repaired) / self.__num_events_produced > 10:
            sys.stderr.write(
                'WARNING: %d out of %d events were automatically repaired because they were invalid. '
                'If performance is important, verify your event generator code to produce valid events.\n' %
                (self.__num_events_repaired, self.__num_events_produced)
            )

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def close_event_group(self):
        """

        Closes a previously opened event group.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        if self.__element_stack[-1] != 'eventgroup':
            self.error(
                'Unbalanced <eventgroup> tag. Did you forget to call CloseEvent()?')
        self.__element_stack.pop()

        # This closes the generator, writing the closing eventgroup tag.
        self.__event_group_xml_writer.close()

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def add_event(self, event):
        """

        Adds specified event to the output data stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          event (edxml.EDXMLEvent): The event

        Returns:
          unicode: Generated output XML data

        """
        if self.__element_stack[-1] != 'eventgroup':
            self.error(
                'A <event> tag must be child of an <eventgroup> tag. Did you forget to call OpenEventGroup()?')

        if isinstance(event, etree._Element):
            event_element = event
        elif isinstance(event, edxml.EDXMLEvent):
            event = edxml.EventElement(
                event.get_properties(), parents=event.get_explicit_parents(), content=event.get_content()
            )
            event_element = event.get_element()
        elif isinstance(event, edxml.EventElement):
            event_element = event.get_element()
        else:
            raise TypeError('Unknown type of event: %s' % str(type(event)))

        if self.__validate:
            if not self.__event_type_schema.validate(event_element):
                # Event does not validate.
                try:
                    # Try to repair the event by normalizing the object
                    # values.
                    if self.__log_repaired_events:
                        original_event = deepcopy(event)
                        self.__ontology.get_event_type(self.__current_event_type_name).normalize_event_objects(event)
                        for property_name in original_event.keys():
                            if event[property_name] != original_event[property_name]:
                                sys.stderr.write(
                                    'Repaired invalid property %s of event type %s: %s => %s\n' %
                                    (property_name, self.__current_event_type_name, repr(
                                        original_event[property_name]), repr(event[property_name]))
                                )
                    else:
                        self.__ontology.get_event_type(self.__current_event_type_name).normalize_event_objects(event)

                except EDXMLValidationError:
                    # Repairing failed.
                    self.__generate_event_validation_exception(
                        event, event_element)
                else:
                    # Repairing succeeded. For the time being, just to be sure,
                    # we validate the event again.
                    # TODO: Remove this second validation once normalize_event_objects()
                    # is known to yield valid object values in all cases.
                    if not self.__event_type_schema.validate(event_element):
                        self.__generate_event_validation_exception(
                            event, event_element)
                    self.__num_events_repaired += 1

        try:
            self.__event_group_xml_writer.send(event_element)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.__num_events_produced += 1

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def close_event_groups(self):
        """

        Closes a previously opened <eventgroups> element.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data

        """
        if self.__element_stack[-1] != 'eventgroups':
            self.error(
                'Unbalanced <eventgroups> tag. Did you forget to call close_event_group()?')
        self.__element_stack.pop()
        # We send None to the outer XML generator, to
        # hint it that the eventgroups element has been
        # completed and we want it to generate the
        # eventgroups closing tag.
        try:
            self.__writer.send(None)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''
