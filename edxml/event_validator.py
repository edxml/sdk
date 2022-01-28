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
from lxml import etree
from typing import Dict, Optional

import edxml
from edxml.error import EDXMLEventValidationError


class EventValidatorError:
    """
    Class representing EDXML event validation errors
    """
    def __init__(self, exception, schema_error, property_name, attachment_name):
        self.exception = exception
        """The exception that was raised"""
        self.schema_error = schema_error  # type: etree._LogEntry
        """The last error from the error log of the RelaxNG schema"""
        self.property_name = property_name
        """The invalid property, if any"""
        self.attachment_name = attachment_name
        """The invalid attachment, if any"""


class EventValidator:
    """
    Class for validating EDXML events.
    """

    def __init__(self, ontology):
        self.__ontology = ontology  # type: edxml.ontology.Ontology
        self.__ontology_version = 0

        self.__event_type_schema_cache = {}     # type: Dict[str, etree.RelaxNG]
        self.__event_type_schema_cache_ns = {}  # type: Dict[str, etree.RelaxNG]

        self.__last_error = None  # type: Optional[EventValidatorError]

    def validate(self, event, event_element=None):
        """

        Validates given event, raising an exception in case the event
        is invalid. If you happen to have the XML representation of the event
        at hand you can pass it along for improved efficiency.

        Args:
            event (edxml.EDXMLEvent): The event that will be validated
            event_element (lxml.etree._Element): The XML representation of the event

        Raises:
                EDXMLEventValidationError:

        """
        event_element = event_element if event_element is not None else event.get_element()
        event_type_name = event.get_type_name()
        # Parsed events inherit the global namespace from the
        # EDXML data stream that they originate from. Unfortunately,
        # the lxml XML generator (specifically etree.xmlfile) is not
        # so clever as to filter out these namespaces when writing into
        # an output stream that already has a global namespace. So,
        # for this specific case, we must write explicitly namespaced
        # events and use a separate validation schema.
        schema = self._get_event_type_schema(event_type_name, namespaced=isinstance(event, edxml.event.ParsedEvent))

        if not schema.validate(event_element):
            # Event does not validate.
            self._generate_event_validation_exception(event, event_element, schema)

    def is_valid(self, event, event_element=None):
        """

        Validates given event, returning True for valid events or False for invalid
        events. If you happen to have the XML representation of the event
        at hand you can pass it along for improved efficiency.

        Args:
            event (edxml.EDXMLEvent): The event that will be validated
            event_element (lxml.etree._Element): The XML representation of the event

        Returns:
            bool: Valid yes / no
        """
        try:
            self.validate(event, event_element)
        except EDXMLEventValidationError:
            return False
        else:
            return True

    def get_last_error(self):
        """

        Returns the last error produced by the validator.

        Returns:
            EventValidatorError:
        """
        return self.__last_error

    def _get_event_type_schema(self, event_type_name, namespaced):
        if self.__ontology.get_version() > self.__ontology_version:
            # Ontology was updated, clear cache.
            self.__event_type_schema_cache = {}
            self.__event_type_schema_cache_ns = {}

        schema_cache = self.__event_type_schema_cache_ns if namespaced else self.__event_type_schema_cache
        if event_type_name not in schema_cache:
            schema_cache[event_type_name] = etree.RelaxNG(
                self.__ontology.get_event_type(event_type_name).generate_relax_ng(self.__ontology, namespaced)
            )

        return schema_cache[event_type_name]

    def _generate_event_validation_exception(self, event, event_element, schema):

        exception = None
        property_name = None
        attachment_name = None

        try:
            if schema.error_log.last_error.path.startswith('/event/properties/'):
                # Something is wrong with event properties.
                property_name = schema.error_log.last_error.path.split('/')[-1].split('[')[0]
                self.__ontology.get_event_type(event.get_type_name()).validate_event_objects(event, property_name)
            elif schema.error_log.last_error.path.startswith('/event/attachments/'):
                # Something is wrong with event attachments.
                attachment_name = schema.error_log.last_error.path.split('/')[-1].split('[')[0]
                self.__ontology.get_event_type(event.get_type_name()).validate_event_attachments(event, attachment_name)

            # Maybe there is a problem with the event structure, like a single-valued
            # property having multiple object values.
            # TODO: We do not populate property_name and attachment_name in this case yet.
            self.__ontology.get_event_type(event.get_type_name()).validate_event_structure(event)

            # Check the attributes of the event element.
            for event_attrib_name, event_attrib_value in event_element.attrib.items():
                if event_attrib_name not in ['event-type', 'source-uri']:
                    # Must be a faulty foreign attribute.
                    if not event_attrib_name.startswith('{'):
                        raise EDXMLEventValidationError(
                            f"Event contains a foreign attribute without a namespace: "
                            f"{event_attrib_name} = {event_attrib_value}"
                        )
                    if event_attrib_name.startswith('{http://edxml.org/edxml}'):
                        raise EDXMLEventValidationError(
                            f"Event contains a foreign attribute with an EDXML namespace: "
                            f"{event_attrib_name} = {event_attrib_value}"
                        )

        except EDXMLEventValidationError as error:
            exception = error

        if not exception:

            # EventType validation did not find the issue. We have
            # no other option than to raise a RelaxNG validation error.
            exception = EDXMLEventValidationError(
                "At xpath location %s: %s" %
                (
                    schema.error_log.last_error.path,
                    schema.error_log.last_error.message
                )
            )

        self.__last_error = EventValidatorError(exception, schema.error_log.last_error, property_name, attachment_name)

        raise exception
