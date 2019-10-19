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

from typing import Dict

import edxml

from lxml import etree
from copy import deepcopy
from EDXMLBase import EDXMLBase, EvilCharacterFilter, EDXMLValidationError
from edxml.event import ParsedEvent
from edxml.ontology import Ontology


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

    def __init__(self, output=None, validate=True, log_repaired_events=False, ignore_invalid_objects=False,
                 pretty_print=True):

        super(EDXMLWriter, self).__init__()

        self.__ontology = Ontology()            # type: Ontology
        self.__event_type_schema_cache = {}     # type: Dict[str, etree.RelaxNG]
        self.__event_type_schema_cache_ns = {}  # type: Dict[str, etree.RelaxNG]
        self.__ignore_invalid_objects = ignore_invalid_objects
        self.__log_repaired_events = log_repaired_events
        self.__invalid_event_count = 0
        self.__pretty_print = pretty_print
        self.__validate = validate
        self.__output = output

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
        self.__writer = self.__outer_xml_serializer_coroutine()
        self.__writer.next()

        self.__current_element_type = ""
        self.__event_types = {}
        self.__object_types = {}

    def get_output(self):
        return self.__output

    def get_event_type_schema(self, event_type_name, namespaced):
        if event_type_name not in self.__event_type_schema_cache:
            self.__event_type_schema_cache[event_type_name] = etree.RelaxNG(
                self.__ontology.get_event_type(event_type_name).generate_relax_ng(self.__ontology, namespaced=False)
            )

        if event_type_name not in self.__event_type_schema_cache_ns:
            self.__event_type_schema_cache_ns[event_type_name] = etree.RelaxNG(
                self.__ontology.get_event_type(event_type_name).generate_relax_ng(self.__ontology, namespaced=True)
            )

        if namespaced:
            return self.__event_type_schema_cache_ns.get(event_type_name)
        else:
            return self.__event_type_schema_cache.get(event_type_name)

    def __generate_event_validation_exception(self, event, event_element, schema):
        try:
            self.__ontology.get_event_type(event.get_type_name()).validate_event_structure(event)

            # EventType structure checks out alright. Let us check the object values.
            self.__ontology.get_event_type(event.get_type_name()).validate_event_objects(event)

            # Objects also appear to be OK. Let us check the attachments.
            self.__ontology.get_event_type(event.get_type_name()).validate_event_attachments(event)

            # EventType validation did not find the issue. We have
            # no other option than to raise a RelaxNG validation error.
            raise EDXMLValidationError(
                "At xpath location %s: %s" %
                (
                    schema.error_log.last_error.path,
                    schema.error_log.last_error.message
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
            with writer.element('edxml', version='3.0.0', nsmap=edxml.namespace):
                writer.flush()
                try:
                    while True:
                        # This is the main loop which generates the ontology elements,
                        # event elements and foreign elements.
                        writer.write((yield), pretty_print=self.__pretty_print)
                        writer.flush()
                        if not self.__pretty_print:
                            self.__output.write('\n')
                except GeneratorExit:
                    # Coroutine was closed
                    pass

    def flush(self):
        if isinstance(self.__output, self.OutputBuffer):
            output = u''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return u''

    def add_ontology(self, ontology):
        """

        Writes an EDXML ontology element into the output.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          ontology (edxml.ontology.Ontology): The ontology

        Returns:
          unicode: Generated output XML data

        """
        # Below updates triggers an exception in case the update
        # is incompatible or otherwise invalid.
        self.__ontology.update(ontology)

        try:
            self.__writer.send(ontology.generate_xml())
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.__event_type_schema_cache = {}
        self.__event_type_schema_cache_ns = {}

        return self.flush()

    def close(self):
        """

        Finalizes the output data stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        self.__writer.close()

        if self.__num_events_produced > 0 and (100 * self.__num_events_repaired) / self.__num_events_produced > 10:
            sys.stderr.write(
                'WARNING: %d out of %d events were automatically repaired because they were invalid. '
                'If performance is important, verify your event generator code to produce valid events.\n' %
                (self.__num_events_repaired, self.__num_events_produced)
            )

        return self.flush()

    def _repair_event(self, event, schema):
        """

        Tries to repair an invalid event by normalizing object
        values. In case the writer is configured to ignore invalid
        objects, it may try to remove invalid objects in case
        normalization fails.

        Raises EDXMLValidationError in case the repair operation failed.

        Args:
            event (edxml.EventElement): The event
            schema (ElementTree): The RelaxNG schema for the event
        """

        while not schema.validate(event.get_element()):

            original_event = deepcopy(event)

            try:
                # Try to repair the event by normalizing the object values. This throws
                # an EDXMLValidationError in case any value does not make sense.
                self.__ontology.get_event_type(event.get_type_name()).normalize_event_objects(event)
                if event.get_properties() == original_event.get_properties():
                    raise EDXMLValidationError("Normalization did not change anything.")
            except EDXMLValidationError:
                # normalization failed.
                last_error = schema.error_log.last_error

                if last_error.path is None or \
                        not last_error.path.startswith('/event/properties/') or \
                        not self.__ignore_invalid_objects:
                    # Either we have no idea what is wrong, or we cannot do anything about it.
                    # Raise a validation exception.
                    self.__generate_event_validation_exception(event, event.get_element(), schema)

                # Try removing the offending property object.
                for invalid_element in event.get_element().xpath(last_error.path):
                    invalid_element.getparent().remove(invalid_element)
                    if self.__log_repaired_events:
                        sys.stderr.write(
                            "Removed invalid object '%s' of property '%s'.\n" %
                            (invalid_element.text, invalid_element.tag)
                        )

                if self.__log_repaired_events:
                    for property_name in original_event.keys():
                        if event[property_name] != original_event[property_name]:
                            sys.stderr.write(
                                'Repaired invalid property %s of event type %s: %s => %s\n' %
                                (property_name, event.get_type_name(), repr(
                                    original_event[property_name]), repr(event[property_name]))
                            )

        self.__num_events_repaired += 1

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
        # Below, we make sure that 'event' refers to an EDXMLEvent object
        # while 'event_element' is a reference to the internal lxml element
        # representation of 'event'.
        if isinstance(event, ParsedEvent):
            event_element = event
        elif isinstance(event, edxml.EventElement):
            event_element = event.get_element()
        elif isinstance(event, edxml.EDXMLEvent):
            event = edxml.EventElement.create_from_event(event)
            event_element = event.get_element()
        else:
            raise TypeError('Unknown type of event: %s' % str(type(event)))

        event_type_name = event.get_type_name()
        source_uri = event.get_source_uri()

        if event_type_name is None:
            raise EDXMLValidationError(
                'Attempt to add an event that has no event type set. '
                'Please check that the event generator is configured '
                'to set the event type for each output event.'
            )

        if source_uri is None:
            raise EDXMLValidationError(
                'Attempt to add an event that has no event source set. '
                'Please check that the event generator is configured '
                'to set the event source for each output event.'
            )

        if self.__ontology.get_event_type(event_type_name) is None:
            raise EDXMLValidationError(
                'Attempt to add an event using unknown event type: "%s"' % event_type_name)

        if self.__ontology.get_event_source(source_uri) is None:
            raise EDXMLValidationError(
                'Attempt to add an event using unknown source URI: "%s"' % source_uri)

        if self.__validate:
            # Parsed events inherit the global namespace from the
            # EDXML data stream that they originate from. Unfortunately,
            # the lxml XML generator (specifically etree.xmlfile) is not
            # so clever as to filter out these namespaces when writing into
            # an output stream that already has a global namespace. So,
            # for this specific case, we must write explicitly namespaced
            # events and use a separate validation schema.
            schema = self.get_event_type_schema(event_type_name, isinstance(event, ParsedEvent))

            if not schema.validate(event_element):
                # Event does not validate. We will try to repair it. Note that, since event_element
                # is a reference to the internal lxml element, the repair action will manipulate
                # event_element.
                self._repair_event(event, schema)

        try:
            self.__writer.send(event_element)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.__num_events_produced += 1

        return self.flush()

    def add_foreign_element(self, element):
        """

        Adds specified foreign element to the output data stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          element (etree._Element): The element

        Returns:
          unicode: Generated output XML data

        """
        try:
            self.__writer.send(element)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        return self.flush()
