# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                     Python class for parsing EDXML data
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

"""
This module offers various classes for incremental parsing of EDXML data streams.
"""
import os
import re
import sys
import edxml

from collections import defaultdict
from copy import deepcopy
from lxml import etree
from EDXMLBase import EDXMLValidationError
from edxml import ParsedEvent


class ProcessingInterrupted(Exception):
    pass


class EDXMLParserBase(object):
    """
    This is the base class for all EDXML parsers.
    """

    def __init__(self, validate=True):
        """
        Create a new EDXML parser. By default, the parser
        validates the input. Validation can be disabled
        by setting validate = False

        Args:
          validate (bool, optional): Validate input or not
        """

        self._ontology = None                # type: edxml.ontology.Ontology
        self._element_iterator = None         # type: etree.Element
        self._event_class = None

        self.__current_event_type = None       # type: str
        self.__current_event_source_uri = None  # type: str
        self.__current_event_source = None     # type: edxml.ontology.EventSource
        self.__current_group_event_count = 0    # type: int
        self.__root_element = None            # type: etree.Element
        self.__current_group_element = None    # type: etree.Element
        self.__event_groups_element = None     # type: etree.Element
        self.__previous_root_length = None
        self.__num_parsed_events = 0           # type: int
        self.__num_parsed_event_types = {}      # type: Dict[str, int]
        self.__event_type_handlers = {}        # type: Dict[str, callable]
        self.__event_source_handlers = {}      # type: Dict[str, callable]
        self.__current_event_handlers = []     # type: List[callable]
        self.__source_uri_pattern_map = {}      # type: Dict[Any, List[str]]

        self.__schema = None                 # type: etree.RelaxNG
        self.__event_type_schema_cache = {}     # type: Dict[str, etree.RelaxNG]
        self.__event_type_schema = None        # type: etree.RelaxNG

        self.__validate = validate           # type: bool

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Note that, below, we check if an exception occurred.
        # We only perform the final global document structure
        # validation when no error occurred, because the validator
        # may not have consumed all of its input due to this
        # exception. Python will destruct the parser context before
        # the exception reaches its handler. Validation might throw
        # a second exception complaining about the document being
        # invalid, masking the original problem.
        if exc_type is None:
            self.__validate_root_element()
            self._close()

    def _close(self):
        """

        Callback that is invoked when the parsing process is
        finished or interrupted.

        Returns:
          EDXMLParserBase: The EDXML parser

        """
        return self

    def set_event_type_handler(self, event_types, handler):
        """

        Register a handler for specified event types. Whenever
        an event is parsed of any of the specified types, the
        supplied handler will be called with the event (which
        will be a ParsedEvent instance) as its only argument.

        Multiple handlers can be installed for a given type of
        event, they will be invoked in the order of registration.
        Event type handlers are invoked before event source handlers.

        Args:
          event_types (List[str]): List of event type names
          handler (callable): Handler

        Returns:
          EDXMLParserBase: The EDXML parser

        """
        for eventType in event_types:
            if eventType not in self.__event_type_handlers:
                self.__event_type_handlers[eventType] = []
            self.__event_type_handlers[eventType].append(handler)

        return self

    def set_event_source_handler(self, source_patterns, handler):
        """

        Register a handler for specified event sources. Whenever
        an event is parsed that has an event source URI matching
        any of the specified regular expressions, the supplied
        handler will be called with the event (which will be a
        ParsedEvent instance) as its only argument.

        Multiple handlers can be installed for a given event source,
        they will be invoked in the order of registration. Event source
        handlers are invoked after event type handlers.

        Args:
          source_patterns (List[str]): List of regular expressions
          handler (callable): Handler

        Returns:
          EDXMLParserBase: The EDXML parser

        """
        for pattern in source_patterns:
            if pattern not in self.__event_source_handlers:
                self.__event_source_handlers[pattern] = []
            self.__event_source_handlers[pattern].append(handler)

        return self

    def set_custom_event_class(self, event_class):
        """

        By default, EDXML parsers will generate ParsedEvent
        instances for representing event elements. When this
        method is used to set a custom element class, this
        class will be instantiated in stead of etree.Element.
        This can be used to implement custom APIs on top of
        the EDXML events that are generated by the parser.

        Note:
          In is strongly recommended to extend the ParsedEvent
          class and implement additional class methods on top
          of it.

        Note:
          Implementing a custom element class that can replace
          the standard etree.Element class is tricky, be sure to
          read the lxml documentation about custom Element
          classes.

        Args:
          event_class (etree.ElementBase): The custom element class

        Returns:
          EDXMLParserBase: The EDXML parser

        """
        self._event_class = event_class
        return self

    def get_event_counter(self):
        """

        Returns the number of parsed events. This counter
        is incremented after the _parsedEvent callback returned.

        Returns:
          int: The number of parsed events
        """
        return self.__num_parsed_events

    def get_event_type_counter(self, event_type_name):
        """

        Returns the number of parsed events of the specified
        event type. These counters are incremented after the
        _parsedEvent callback returned.

        Args:
          event_type_name (str): The type of parsed events

        Returns:
          int: The number of parsed events
        """
        return self.__num_parsed_event_types.get(event_type_name, 0)

    def get_ontology(self):
        """

        Returns the ontology that was read by the parser, or
        None if no ontology has been read yet.

        Note:
          The ontology will not be available until the first
          event has been parsed.

        Returns:
           edxml.ontology.Ontology: The parsed ontology
        """
        return self._ontology

    def get_event_type_schema(self, event_type_name):
        """

        Returns the RelaxNG schema that is used by the parser
        to validate the specified event type. Returns None if
        the event type is not known to the parser.

        Args:
          event_type_name (str):

        Returns:
          etree.RelaxNG:
        """
        if event_type_name not in self.__event_type_schema_cache:
            self.__event_type_schema_cache[event_type_name] = etree.RelaxNG(
                self._ontology.get_event_type(event_type_name).generate_relax_ng(self._ontology)
            )
        return self.__event_type_schema_cache.get(event_type_name)

    def __find_root_element(self, event_element):
        # Find the root element by traversing up the
        # tree. The first parent element that we will
        # find this way is the eventgroup tag that
        # contains the current event.
        self.__root_element = event_element.getparent()
        while self.__root_element is not None and self.__root_element.tag != 'edxml':
            self.__root_element = self.__root_element.getparent()
        if self.__root_element is None or self.__root_element.tag != 'edxml':
            raise EDXMLValidationError(
                'Invalid EDXML structure detected: Could not find the edxml root tag.')

    def __validate_root_element(self):
        # Note that this method can only be called after
        # parsing is completed. At any other stage in the
        # parsing process, the tree structure is incomplete.
        if not self.__schema:
            self.__schema = etree.RelaxNG(
                etree.parse(os.path.dirname(os.path.realpath(
                    __file__)) + '/schema/edxml-schema-3.0.0.rng')
            )

        try:
            self.__schema.assertValid(self.__root_element)
        except (etree.DocumentInvalid, etree.XMLSyntaxError) as ValidationError:
            # XML structure is invalid.
            raise EDXMLValidationError(
                "Invalid EDXML structure detected: %s\nThe RelaxNG validator generated the following error: %s" %
                (etree.tostring(self.__root_element), str(ValidationError))
            )

    def __validate_definitions_element(self, ontology_element):
        if not self.__schema:
            self.__schema = etree.RelaxNG(
                etree.parse(os.path.dirname(os.path.realpath(
                    __file__)) + '/schema/edxml-schema-3.0.0.rng')
            )

        # Since lxml iterparse gives us partial XML
        # trees, elements from which we have not seen
        # its closing tag yet may not be valid yet. So,
        # we integrate the ontology element into a
        # skeleton tree, yielding a complete, valid
        # EDXML structure.
        skeleton = etree.Element('edxml', attrib=self.__root_element.attrib)
        skeleton.append(deepcopy(ontology_element))
        etree.SubElement(skeleton, 'eventgroups')

        try:
            self.__schema.assertValid(skeleton)
        except (etree.DocumentInvalid, etree.XMLSyntaxError) as ValidationError:
            # XML structure is invalid.
            raise EDXMLValidationError(
                "Invalid EDXML structure detected: %s\nThe RelaxNG validator generated the following error: %s" %
                (etree.tostring(self.__root_element), str(ValidationError))
            )

    def __process_ontology(self, ontology_element):
        preceding_event_groups_element = ontology_element.getprevious()
        if preceding_event_groups_element is not None:
            preceding_definitions_element = preceding_event_groups_element.getprevious()
            if preceding_definitions_element is None:
                # XML structure is invalid, because there must be
                # an ontology element preceding the eventgroups element.
                raise EDXMLValidationError(
                    "EDXML structure contains an ontology element without a preceding eventgroups element: %s\n" %
                    (etree.tostring(self.__root_element))
                )

            # We have one complete pair of an ontology and
            # an eventgroups element preceding the current ontology
            # element. We can safely delete them.
            del self.__root_element[0:2]

        # Before parsing the ontology information, we validate
        # the generic structure of the ontology element, using
        # the RelaxNG schema.
        self.__validate_definitions_element(ontology_element)

        # We survived XML structure validation. We can proceed
        # and process the new ontology information.
        if self._ontology is None:
            self._ontology = edxml.ontology.Ontology()

        try:
            self._ontology.update(ontology_element)
            self.__event_type_schema_cache = {}
        except EDXMLValidationError as exception:
            exception.message = "Invalid ontology definition detected: %s\n%s" %\
                                (etree.tostring(ontology_element,
                                                pretty_print=True), exception.message)
            raise

        for eventTypeName in self._ontology.get_event_type_names():
            self.__num_parsed_event_types[eventTypeName] = 0

        # Invoke callback to inform about the
        # new ontology.
        self._parsed_ontology(self._ontology)

        # Use the ontology to build a mapping of event
        # handler source patterns to source URIs
        self.__source_uri_pattern_map = defaultdict(list)
        for pattern in self.__event_source_handlers.keys():
            for sourceUri, source in self._ontology.get_event_sources():
                if re.match(pattern, sourceUri):
                    self.__source_uri_pattern_map[pattern].append(sourceUri)

    def _parsed_ontology(self, ontology):
        """
        Callback that is invoked when the ontology has
        been updated from input data. The passed ontology
        contains the result of merging all ontology information
        that has been parsed so far.

        Args:
          ontology (edxml.ontology.Ontology): The parsed ontology
        """
        # Since an override of this method may call this parent
        # method passing a different ontology, we assign it here.
        self._ontology = ontology

    def _parse_edxml(self):

        for action, elem in self._element_iterator:

            if self.__root_element is None:
                self.__find_root_element(elem)

            if elem.tag == 'edxml':
                if elem.getparent() is None:
                    version_string = elem.attrib['version']
                    if version_string is None:
                        raise EDXMLValidationError(
                            'Root element is missing the version attribute.')
                    version = version_string.split('.')
                    if len(version) != 3:
                        raise EDXMLValidationError(
                            'Root element contains invalid version attribute: "%s"' % version_string)
                    if int(version[0]) != 3 or int(version[1]) > 0:
                        raise EDXMLValidationError(
                            'Unsupported EDXML version: "%s"' % version_string)
                continue

            if elem.tag == 'event':
                if elem.getparent().tag == 'eventgroup':
                    if self.__current_group_element is None:
                        # Apparently, we did not parse the current event group
                        # yet.
                        self.__parse_event_group(elem.getparent())

                    if self.__current_event_type is not None and self.__current_event_source_uri is not None:
                        elem.set_type(self.__current_event_type).set_source(
                            self.__current_event_source_uri)
                        self.__parse_event(elem)
                        self.__current_group_event_count += 1
                        if self.__current_group_event_count > 1:
                            # Delete the event tag, unless it is
                            # the first event tag in the event group.
                            # We do not want to delete the event that
                            # we are currently processing, lxml does
                            # not like that.
                            del self.__current_group_element[0]
                            pass
                continue

            if elem.tag == 'eventgroup':
                if elem.getparent().tag == 'eventgroups':
                    if self.__current_group_element is not None:
                        self._close_event_group(
                            self.__current_event_type, self.__current_event_source_uri)
                        self.__current_group_event_count = 0
                    self.__current_group_element = None
                    self.__current_event_type = None
                    self.__current_event_source = None
                    self.__current_event_source_uri = None
                continue

            if elem.tag == 'ontology':
                if elem.getparent().tag == 'edxml':
                    self.__process_ontology(elem)
                continue

    def __parse_event_group(self, group_element):

        if self.__current_group_element is not None:
            self._close_event_group(self.__current_event_type,
                                    self.__current_event_source_uri)

        # Since lxml iterparse gives us partial XML
        # trees, elements from which we have not seen
        # its closing tag yet may not be valid yet. For
        # that reason, we cannot use the EDXML RelaxNG
        # schema to validate the full XML structure while
        # parsing is still in progress. Hence the explicit
        # attribute validation here.

        event_type_name = group_element.attrib.get('event-type', '')
        source_uri = group_element.attrib.get('source-uri', '')
        if not re.match(edxml.ontology.EventType.NAME_PATTERN.pattern, event_type_name):
            raise EDXMLValidationError(
                'An eventgroup tag has an invalid event-type attribute: "%s"' % event_type_name)
        if not re.match(edxml.ontology.EventSource.SOURCE_URI_PATTERN.pattern, source_uri):
            raise EDXMLValidationError(
                'An eventgroup tag has an invalid source-uri attribute: "%s"' % source_uri)

        self.__current_group_element = group_element
        self._open_event_group(
            group_element.attrib['event-type'], group_element.attrib['source-uri'])

        if self.__current_event_type is None and self.__current_event_source_uri is None:
            # This may happen when an extension of this
            # class 'swallows' an event group.
            self.__current_event_source = None
            self.__current_event_source_uri = None
            self.__event_type_schema = None
            return

        self.__current_event_source = self._ontology.get_event_source(
            self.__current_event_source_uri)

        if self.__current_event_source is None:
            raise EDXMLValidationError(
                "An eventgroup refers to Source URI %s, which is not defined." % self.__current_event_source_uri
            )
        if self._ontology.get_event_type(self.__current_event_type) is None:
            raise EDXMLValidationError(
                "An eventgroup refers to eventtype %s, which is not defined." % self.__current_event_type
            )

        self.__current_event_source_uri = self.__current_event_source.get_uri()

        if self.__validate:
            self.__event_type_schema = self.get_event_type_schema(
                self.__current_event_type)

    def _close_event_group(self, event_type_name, event_source_uri):
        """

        Callback that is invoked whenever an open event group
        is closed. The event type name and source URI match the
        values that were passed to _open_event_group().

        Args:
          event_type_name (str): The event type name
          event_source_uri (str): URI of the event source

        """
        pass

    def _open_event_group(self, event_type_name, event_source_uri):
        """

        Callback that is invoked whenever a new event group
        is opened, containing events of the specified event type
        and source. Extensions may override this method and call
        this parent method to change the event type or event source
        of the event group.

        When both the event type and source in the call to the
        parent method are None, the parser will ignore the entire
        event group. This implies that no callbacks will be generated
        for the events contained inside it. When the closing tag of
        the group is parsed, the _close_event_group callback is
        invoked normally.

        Args:
          event_type_name (str): The event type name
          event_source_uri (str): URI of the event source

        """
        self.__current_event_type = event_type_name
        self.__current_event_source_uri = event_source_uri

        self.__current_event_handlers = []

        if self.__current_event_type and self.__current_event_source_uri:

            # Add handlers for the event type
            self.__current_event_handlers.extend(
                self.__event_type_handlers.get(self.__current_event_type, ()))

            # Add handlers for the event source
            for pattern, handlers in self.__event_source_handlers.iteritems():
                if self.__current_event_source_uri in self.__source_uri_pattern_map[pattern]:
                    self.__current_event_handlers.extend(handlers)

        if len(self.__current_event_handlers) == 0:
            # No handlers found, check if the empty
            # _parsed_event() method has been overridden
            # by a class extension, so we can use that
            # for handling events.
            this_method = getattr(self, '_parsed_event')
            base_method = getattr(EDXMLParserBase, '_parsed_event')
            if this_method.__func__ is not base_method.__func__:
                self.__current_event_handlers.append(self._parsed_event)

    def __parse_event(self, event):
        if self.__validate and self.__event_type_schema is not None:
            if not self.__event_type_schema.validate(event):
                # Event does not validate. Try to generate a validation
                # exception that is more readable than the RelaxNG
                # error is, by validating using the EventType class.
                try:
                    self._ontology.get_event_type(self.__current_event_type).validate_event_structure(event)

                    # EventType structure checks out alright. Let us check the object values.
                    self._ontology.get_event_type(self.__current_event_type).validate_event_objects(event)

                    # EventType validation did not find the issue. We have
                    # no other option than to raise a RelaxNG error containing
                    # a undoubtedly cryptic error message.
                    raise EDXMLValidationError(
                        self.__event_type_schema.error_log)

                except EDXMLValidationError as exception:
                    schema = self._ontology.get_event_type(
                        self.__current_event_type
                    ).generate_relax_ng(self._ontology)
                    raise EDXMLValidationError('Event failed to validate:\n%s\n\n%s\nSchema:\n%s' % (
                        etree.tostring(event, pretty_print=True).encode(
                            'utf-8'), exception,
                        etree.tostring(schema, pretty_print=True)), sys.exc_info()[2])

        # Call all event handlers in order
        for handler in self.__current_event_handlers:
            handler(event)

        self.__num_parsed_events += 1
        if self.__current_event_type:
            self.__num_parsed_event_types[self.__current_event_type] += 1

    def _parsed_event(self, event):
        """

        Callback that is invoked for every event that is parsed
        from the input EDXML stream.

        Args:
          event (edxml.ParsedEvent): The parsed event

        """
        pass


class EDXMLPullParser(EDXMLParserBase):
    """

    An blocking, incremental pull parser for EDXML data, for
    parsing EDXML data from file-like objects.

    Note:
      This class extends EDXMLParserBase, refer to that
      class for more details about the EDXML parsing interface.

    """

    def parse(self, input_file):
        """

        Parses the specified file. The file can be any
        file-like object, or the name of a file that should
        be opened and parsed. The parser will generate calls
        to the various callback methods in the base class,
        allowing the parsed data to be processed.

        Notes:
          Passing a file name rather than a file-like object
          is preferred and may result in a small performance gain.

        Args:
          input_file (Union[io.TextIOBase, file, str]):

        """
        self._element_iterator = etree.iterparse(
            input_file,
            events=['end'],
            tag=('edxml', 'ontology', 'eventgroup', 'event'),
            no_network=True, resolve_entities=False
        )

        # Set a custom class that lxml should use for
        # representing event elements
        lookup = etree.ElementNamespaceClassLookup()
        if self._event_class is not None:
            lookup.get_namespace('')['event'] = self._event_class
        else:
            lookup.get_namespace('')['event'] = ParsedEvent
        self._element_iterator.set_element_class_lookup(lookup)
        self._parse_edxml()


class EDXMLPushParser(EDXMLParserBase):
    """

    An incremental push parser for EDXML data. Unlike
    the pull parser, this parser does not read data
    by itself and does not block when the data stream
    dries up. It needs to be actively fed with stings,
    allowing full control of the input process.

    Note:
      This class extends EDXMLParserBase, refer to that
      class for more details about the EDXML parsing interface.

    """

    def __init__(self, validate=True):
        super(EDXMLPushParser, self).__init__(validate)
        self.__inputParser = None
        self.__feed_target = None

    def feed(self, data):
        """

        Feeds the specified string to the parser. A call
        to the feed() method may or may not trigger calls
        to callback methods, depending on the size and
        content of the passed string buffer.

        Args:
          data (str): String data

        """
        if self._element_iterator is None:
            self.__inputParser = etree.XMLPullParser(
                events=['end'],
                tag=('event', 'eventgroup', 'ontology'),
                target=self.__feed_target, no_network=True, resolve_entities=False
            )

            # Set a custom class that lxml should use for
            # representing event elements
            lookup = etree.ElementNamespaceClassLookup()
            if self._event_class is not None:
                lookup.get_namespace('')['event'] = self._event_class
            else:
                lookup.get_namespace('')['event'] = ParsedEvent
            self.__inputParser.set_element_class_lookup(lookup)

            self._element_iterator = self.__inputParser.read_events()
        self.__inputParser.feed(data)
        self._parse_edxml()

    def set_feed_target(self, target):
        """

        Sets an optional feed target for the parser.
        The feed target is a class instance which features
        start() and end() methods that return the element
        that is normally generated by the parser itself.
        The feed target may be used to transform the elements
        that are produced by the parser.

        Args:
          target (object): Parse target
        Returns:
          EDXMLPushParser: The parser instance
        """
        # TODO: The lxml library allows the feed target to generate other
        # objects than lxml Element instances, like JSON representations.
        # Implement support for this use case.
        self.__feed_target = target
        return self


class EDXMLOntologyPullParser(EDXMLPullParser):
    """
    A variant of the incremental pull parser which interrupts
    the parsing process when the ontology has been read. It does
    so by raising ProcessingInterrupted.
    It can be used to extract ontology information from EDXML
    data streams and skip reading the event data.
    """

    # TODO: When we get multiple ontology sections in the input,
    # override the parse method to skip all event tags and offer
    # an option to scan the full data stream for ontology info.

    def _parsed_ontology(self, ontology):
        super(EDXMLOntologyPullParser, self)._parsed_ontology(ontology)
        raise ProcessingInterrupted


class EDXMLOntologyPushParser(EDXMLPushParser):
    """
    A variant of the incremental push parser which interrupts
    the parsing process when the ontology has been read. It does
    so by raising ProcessingInterrupted.
    It can be used to extract ontology information from EDXML
    data streams and skip reading the event data.
    """

    # TODO: When we get multiple ontology sections in the input,
    # override the parse method to skip all event tags and offer
    # an option to scan the full data stream for ontology info.

    def _parsed_ontology(self, ontology):
        super(EDXMLOntologyPushParser, self)._parsed_ontology(ontology)
        raise ProcessingInterrupted
