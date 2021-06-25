# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

#
#
#  ===========================================================================
#
#                 Python class for EDXML data stream generation
#
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

"""writer

This module contains the EDXMLWriter class, which is used
to generate EDXML streams.

"""
import edxml_schema
import sys
from collections import deque

from typing import Dict, Optional

from lxml import etree
from copy import deepcopy
from edxml.error import EDXMLEventValidationError, EDXMLOntologyValidationError
from edxml.event import ParsedEvent
from edxml.ontology import Ontology
from edxml.logger import log


NAMESPACE_MAP = {None: 'http://edxml.org/edxml'}


class EDXMLWriter(object):
    """
    Class for generating EDXML streams

    The output parameter is a file-like object that will be used to send the XML data to.
    This file-like object can be pretty much anything, as long as it has a write() method
    and a mode containing 'a' (opened for appending). When the output parameter is omitted,
    the generated XML data will be returned by the methods that generate output.

    The optional validate parameter controls if the generated EDXML stream should be auto-validated
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

        def write(self, data):
            self.buffer.append(data)

    def __init__(self, output=sys.stdout.buffer, validate=True, log_repaired_events=False, pretty_print=True):

        super().__init__()

        self.__schema = None                    # type: Optional[etree.RelaxNG]
        self.__ontology = Ontology()            # type: Ontology
        self.__event_type_schema_cache = {}     # type: Dict[str, etree.RelaxNG]
        self.__event_type_schema_cache_ns = {}  # type: Dict[str, etree.RelaxNG]
        self.__allow_repair_drop = {}
        self.__allow_repair_normalize = {}
        self.__ignore_invalid_events = False
        self.__log_invalid_events = False
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

        # Initialize lxml.etree based XML generator. This
        # will write the XML declaration and the opening
        # <edxml> tag.
        self.__writer = self.__write_coroutine()
        next(self.__writer)

        self.__current_element_type = ""
        self.__event_types = {}
        self.__object_types = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def enable_auto_repair_normalize(self, event_type_name, property_names):
        """

        Enables automatic repair of the property values of events of
        specified type. Whenever an invalid event is generated by the
        mediator it will try to repair the event by normalizing object
        values of specified properties.

        Args:
            event_type_name (str):
            property_names (List[str]):

        Returns:
            edxml.EDXMLWriter
        """
        self.__allow_repair_normalize[event_type_name] = property_names
        return self

    def enable_auto_repair_drop(self, event_type_name, property_names):
        """

        Allows dropping invalid object values from the specified event
        properties while repairing invalid events. This will only be
        done as a last resort when normalizing object values failed or
        is disabled.

        Args:
            event_type_name (str):
            property_names (List[str]):

        Returns:
            edxml.EDXMLWriter
        """
        self.__allow_repair_drop[event_type_name] = property_names
        return self

    def ignore_invalid_events(self, warn=False):
        """

        Instructs the EDXML writer to ignore invalid events.
        After calling this method, any event that fails to
        validate will be dropped. If warn is set to True,
        a detailed warning will be printed, allowing the
        source and cause of the problem to be determined.

        Note:
          This has no effect when event validation is disabled.

        Args:
          warn (bool`, optional): Print warnings or not

        Returns:
           EDXMLWriter: The EDXMLWriter instance
        """
        self.__ignore_invalid_events = True
        self.__log_invalid_events = warn

        return self

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

    def __generate_event_validation_exception(self, event, event_element, schema, property_name=None):
        try:
            if schema.error_log.last_error.path.startswith('/event/properties/'):
                # Something is wrong with event properties.
                self.__ontology.get_event_type(event.get_type_name()).validate_event_objects(event, property_name)
            elif schema.error_log.last_error.path.startswith('/event/attachments/'):
                # Something is wrong with event attachments.
                self.__ontology.get_event_type(event.get_type_name()).validate_event_attachments(event)

            # Something else is wrong.
            self.__ontology.get_event_type(event.get_type_name()).validate_event_structure(event)

            # EventType validation did not find the issue. We have
            # no other option than to raise a RelaxNG validation error.
            raise EDXMLEventValidationError(
                "At xpath location %s: %s" %
                (
                    schema.error_log.last_error.path,
                    schema.error_log.last_error.message
                )
            )

        except EDXMLEventValidationError as exception:
            self.__invalid_event_count += 1
            raise EDXMLEventValidationError(
                'An invalid event was produced:\n%s\n\nThe EDXML validator said: %s\n\n%s' % (
                    etree.tostring(event_element, pretty_print=True, encoding='unicode'),
                    exception,
                    'Note that this exception is not fatal. You can recover by catching the EDXMLValidationError '
                    'and begin writing a new event.'
                )
            )

    def __write_coroutine(self):
        """Coroutine which performs the actual XML serialisation"""
        with etree.xmlfile(self.__output, encoding='utf-8') as writer:
            writer.write_declaration()
            with writer.element('edxml', version='3.0.0', nsmap=NAMESPACE_MAP):
                writer.flush()
                try:
                    while True:
                        # This is the main loop which generates the ontology elements,
                        # event elements and foreign elements.
                        writer.write((yield), pretty_print=self.__pretty_print)
                        writer.flush()
                        if not self.__pretty_print:
                            self.__output.write(b'\n')
                except GeneratorExit:
                    # Coroutine was closed
                    pass

    def flush(self):
        """
        When no output was provided when creating the EDXML writer,
        any generated EDXML data is stored in an internal buffer. In
        that case, this method will return the content of the buffer
        and clear it. Otherwise, an empty string is returned.

        Returns:
            bytes: Generated EDXML data
        """
        if isinstance(self.__output, self.OutputBuffer):
            output = b''.join(self.__output.buffer)
            self.__output.buffer.clear()
            return output
        else:
            return b''

    def add_ontology(self, ontology):
        """

        Writes an EDXML ontology element into the output.

        Args:
          ontology (edxml.ontology.Ontology): The ontology

        Returns:
            edxml.writer.EDXMLWriter:
        """

        # Below update triggers an exception in case the added
        # ontology is invalid or when it is incompatible with
        # the existing ontology.
        self.__ontology.update(ontology)

        ontology_element = ontology.generate_xml()

        if self.__validate:
            edxml = etree.Element('edxml', version='3.0.0', nsmap=NAMESPACE_MAP)
            edxml.append(ontology_element)
            # TODO: Below we make a serialize / deserialize round trip. We
            #       do that because of some namespacing issue that occurs when
            #       we append the ontology element. The resulting <edxml> element
            #       will fail to validate saying "Expecting a namespace for element edxml".
            #       The round trip to XML string and back works around this.
            edxml = etree.fromstring(etree.tostring(edxml))
            if not self.__schema:
                self.__schema = etree.RelaxNG(etree.parse(edxml_schema.SCHEMA_PATH_3_0))
            try:
                self.__schema.assertValid(edxml)
            except (etree.DocumentInvalid, etree.XMLSyntaxError) as validation_error:
                # Ontology does not validate. Apparently there is something
                # odd about it that our own validation did not detect. We have
                # no choice but to generate the schema validation error, which
                # may be slightly cryptic.
                raise EDXMLOntologyValidationError(
                    "Invalid EDXML ontology detected: %s\n"
                    "The RelaxNG validator generated the following error: %s\nDetails: %s" %
                    (
                        etree.tostring(edxml, encoding='unicode', pretty_print=True),
                        str(validation_error),
                        str(validation_error.error_log)
                    )
                )

        self.__writer.send(ontology_element)

        self.__event_type_schema_cache = {}
        self.__event_type_schema_cache_ns = {}

        return self

    def close(self):
        """

        Finalizes the output data stream.

        Returns:
            edxml.writer.EDXMLWriter:

        """
        if self.__writer is None:
            # Already closed
            return

        self.__writer.close()

        if self.__num_events_produced > 0 and (100 * self.__num_events_repaired) / self.__num_events_produced > 10:
            log.warning(
                '%d out of %d events were automatically repaired because they were invalid. '
                'If performance is important, verify your event generator code to produce valid events.\n' %
                (self.__num_events_repaired, self.__num_events_produced)
            )

        self.__writer = None

        return self

    def _repair_event(self, event, schema):
        """

        Tries to repair an invalid event by normalizing object
        values. In case the writer is configured to ignore invalid
        objects, it may try to remove invalid objects in case
        normalization fails.

        Raises EDXMLEventValidationError in case the repair operation failed.

        Args:
            event (edxml.EDXMLEvent): The event
            schema (ElementTree): The RelaxNG schema for the event
        """

        # Do not modify the original event
        event = deepcopy(event)

        while not schema.validate(event.get_element()):

            original_event = deepcopy(event)

            try:
                self._normalize_event(event)
            except EDXMLEventValidationError as e:
                last_error = schema.error_log.last_error

                if last_error.path is None or \
                        not last_error.path.startswith('/event/properties/'):
                    # We have no idea what is wrong. Raise a validation exception.
                    self.__generate_event_validation_exception(event, event.get_element(), schema)

                # Try removing the offending property object(s).
                offending_property_name = last_error.path.split('/')[-1].split('[')[0]

                if offending_property_name not in self.__allow_repair_drop.get(event.get_type_name(), []):
                    # Offending property is not one that we should try to fix.
                    # Raise a validation exception.
                    self.__generate_event_validation_exception(
                        event, event.get_element(), schema, offending_property_name
                    )

                offending_property_values_all = {str(v) for v in event[offending_property_name]}
                offending_property_values_bad = [b.text for b in event.get_element().xpath(last_error.path)]
                event[offending_property_name] = offending_property_values_all.difference(offending_property_values_bad)
                log.info(
                    'Repaired invalid property %s of event type %s (%s): %s => %s\n' % (
                        offending_property_name,
                        event.get_type_name(),
                        str(e),
                        repr(original_event[offending_property_name]),
                        repr(event[offending_property_name])
                    )
                )

        self.__num_events_repaired += 1

        return event

    def _normalize_event(self, event):
        original_event = deepcopy(event)
        normalize_exception = None
        try:
            # Try to repair the event by normalizing the object values. This throws
            # an EDXMLEventValidationError in case any value does not make sense.
            self.__ontology.get_event_type(event.get_type_name())\
                .normalize_event_objects(event, self.__allow_repair_normalize.get(event.get_type_name(), []))
        except EDXMLEventValidationError as e:
            # Normalization failed, but it might have managed to correct one or more
            # objects before failing.
            normalize_exception = e
        if event.get_properties() == original_event.get_properties():
            # Properties did not change, normalization had no effect,
            raise normalize_exception or EDXMLEventValidationError(
                "Attempt to normalize invalid event objects failed."
            )

    def add_event(self, event, sort=False):
        """

        Adds specified event to the output data stream.

        When the sort parameter is set to True, the properties,
        attachments and event parents are sorted as required for
        obtaining the event in its normal form as defined in the
        EDXML specification. While this does not actually output
        the events in their normal form, the sorting does make it
        easier to spot relevant differences between events.

        Args:
          event (edxml.EDXMLEvent): The event
          sort (bool): Sort event components yes or no

        Returns:
            edxml.writer.EDXMLWriter:
        """
        event_type_name = event.get_type_name()
        source_uri = event.get_source_uri()

        if event_type_name is None:
            raise EDXMLEventValidationError(
                'Attempt to add an event that has no event type set. '
                'Please check that the event generator is configured '
                'to set the event type for each output event.'
            )

        if source_uri is None:
            raise EDXMLEventValidationError(
                'Attempt to add an event that has no event source set. '
                'Please check that the event generator is configured '
                'to set the event source for each output event.'
            )

        if self.__ontology.get_event_type(event_type_name) is None:
            raise EDXMLEventValidationError(
                'Attempt to add an event using unknown event type: "%s"' % event_type_name
            )

        if self.__ontology.get_event_source(source_uri) is None:
            raise EDXMLEventValidationError(
                'Attempt to add an event using unknown source URI: "%s"' % source_uri
            )

        event_element = event.get_element(sort)

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
                # Event does not validate.
                if event_type_name not in self.__allow_repair_normalize and not self.__ignore_invalid_events:
                    self.__generate_event_validation_exception(event, event_element, schema)

                # We will try to repair the event. Note that, since event_element
                # is a reference to the internal lxml element, the repair action will manipulate
                # event_element.
                try:
                    event = self._repair_event(event, schema)
                    log.info('Event validated after repairing it.')
                    event_element = event.get_element()
                except EDXMLEventValidationError as error:
                    if self.__ignore_invalid_events:
                        if self.__log_invalid_events:
                            log.info(str(error) + '\n\nContinuing anyways.\n')
                        return self
                    else:
                        raise

        self.__writer.send(event_element)

        self.__num_events_produced += 1

        return self

    def add_foreign_element(self, element):
        """

        Adds specified foreign element to the output data stream.

        Args:
          element (etree._Element): The element

        Returns:
            edxml.writer.EDXMLWriter:
        """
        self.__writer.send(element)

        return self
