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

from lxml.etree import XMLSyntaxError
from typing import Dict, List, Any

import edxml

from collections import defaultdict
from lxml import etree
from edxml.error import EDXMLValidationError
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

        self.__previous_event = None            # type: etree.Element
        self.__root_element = None            # type: etree.Element
        self.__num_parsed_events = 0           # type: int
        self.__num_parsed_event_types = {}      # type: Dict[str, int]
        self.__event_type_handlers = {}        # type: Dict[str, callable]
        self.__event_source_handlers = {}      # type: Dict[str, callable]
        self.__source_uri_pattern_map = {}      # type: Dict[Any, List[str]]
        self.__parsed_initial_ontology = False

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
            self.close()

    def close(self):
        """
        Close the parser after parsing has finished. After closing,
        the parser instance can be reused for parsing another EDXML
        data file.

        Returns:
          EDXMLParserBase: The EDXML parser
        """
        self.__parsed_initial_ontology = False
        self.__root_element = None
        self._close()
        return self

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

        Returns the ontology that was read by the parser. The ontology
        is updated whenever new ontology information is parsed from
        the input data.

        Returns:
           edxml.ontology.Ontology: The parsed ontology
        """
        return self._ontology or edxml.ontology.Ontology()

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
        if event_element.tag == '{http://edxml.org/edxml}edxml' and event_element.getparent() is None:
            # The passed element is the root element.
            self.__root_element = event_element
            return
        # Find the root element by traversing up the
        # tree until the <edxml> tag is found.
        self.__root_element = event_element.getparent()
        while self.__root_element is not None and self.__root_element.tag != '{http://edxml.org/edxml}edxml':
            self.__root_element = self.__root_element.getparent()
        if self.__root_element is None or self.__root_element.tag != '{http://edxml.org/edxml}edxml':
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

        if self.__root_element is None:
            # The root element is set as soon as the opening <edxml> tag
            # is parsed. If it is not set, we either did not receive any
            # XML tags or the input is not valid EDXML.
            raise EDXMLValidationError('Failed to parse EDXML data. Either the data is not EDXML or it is empty.')

        try:
            self.__schema.assertValid(self.__root_element)
        except (etree.DocumentInvalid, etree.XMLSyntaxError) as ValidationError:
            # XML structure is invalid.
            raise EDXMLValidationError(
                "Invalid EDXML structure detected: %s\n"
                "The RelaxNG validator generated the following error: %s\nDetails: %s" %
                (
                    etree.tostring(self.__root_element, encoding='unicode'),
                    str(ValidationError),
                    str(ValidationError.error_log)
                )
            )

    def __process_ontology(self, ontology_element):
        # Before parsing the ontology information, we validate
        # the generic structure of the ontology element, using
        # the RelaxNG schema.
        self.__validate_root_element()

        # We survived XML structure validation. We can proceed
        # and process the new ontology information.
        if self._ontology is None:
            self._ontology = edxml.ontology.Ontology()

        try:
            self._ontology.update(ontology_element)
            self.__event_type_schema_cache = {}
        except EDXMLValidationError as exception:
            exception.message = "Invalid ontology definition detected: %s\n%s" %\
                                (
                                    etree.tostring(ontology_element, pretty_print=True, encoding='unicode'),
                                    exception
                                )
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

            if elem.tag == '{http://edxml.org/edxml}edxml':
                if elem.getparent() is None:
                    version_string = elem.attrib.get('version')
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

            elif elem.tag == '{http://edxml.org/edxml}event':
                if type(elem) != ParsedEvent:
                    raise TypeError("The parser instantiated a regular lxml Element in stead of a ParsedEvent")

                if elem.getparent().tag != '{http://edxml.org/edxml}edxml':
                    # We expect <event> tags to be children of the root <edxml>
                    # tag. This is not the case here.
                    self._parse_misplaced_event(elem)

                if self._ontology is None:
                    # We are about to parse an event without any preceding
                    # ontology element. This is not valid EDXML.
                    raise EDXMLValidationError("Found an <event> element while no <ontology> has been read yet.")

                self.__parse_event(elem)

                # The first child of the root is always an <ontology> element. We do not
                # clean that one, because that would render our EDXML tree structure invalid.
                # This means that the events that we are processing are always the second
                # child of the root element. However, deleting the element that we are
                # currently processing can lead to crashes in lxml. So, we only delete
                # the second event, which is the third child of the root.
                if self.__num_parsed_events > 1:
                    del self.__root_element[1]

            elif elem.tag == '{http://edxml.org/edxml}ontology':
                if elem.getparent().tag != '{http://edxml.org/edxml}edxml':
                    raise EDXMLValidationError("Found a misplaced <ontology> element.")
                self.__process_ontology(elem)
                # Now that we parsed an <ontology> element, we want to delete it from
                # the XML tree. Unless it is the first <ontology> element we come across,
                # because deleting that element yields an invalid EDXML structure. Since
                # we never delete the initial <ontology> element and always delete events
                # after processing them, any subsequent <ontology> elements will be the
                # second child in the tree:
                #
                # <edxml>
                #   <ontology/>   # <-- initial ontology
                #   <ontology/>   # <-- second / third / ... ontology
                #   ...
                # </edxml>
                #
                # So, we delete the second child of the root element unless it is the
                # initial <ontology> element.
                if self.__parsed_initial_ontology:
                    del self.__root_element[1]
                else:
                    self.__parsed_initial_ontology = True

            elif not elem.tag.startswith('{http://edxml.org/edxml}'):
                if not elem.tag.startswith('{'):
                    raise EDXMLValidationError("Parser received an element without an XML namespace: '%s'" % elem.tag)
                # We have a foreign element.
                self._parse_foreign_element(elem)

            else:
                raise EDXMLValidationError('Parser received unexpected element with tag %s' % elem.tag)

    def _parse_misplaced_event(self, elem):
        # We expect <event> tags to be children of the root <edxml>
        # tag. When this is not the case, there are two possibilities.
        # either we hit an event property that just happens to be
        # named 'event' or we have invalid EDXML. In case of an event
        # property, we just ignore it here. Otherwise, we fail.
        parents = []
        while elem is not None:
            parents.append(elem.tag)
            elem = elem.getparent()
        if parents != [
            '{http://edxml.org/edxml}event',
            '{http://edxml.org/edxml}properties',
            '{http://edxml.org/edxml}event',
            '{http://edxml.org/edxml}edxml'
        ]:
            raise EDXMLValidationError(
                'Unexpected <event> tag. This is neither an EDXML event '
                'nor an event property named "event".'
            )

    def _get_event_handlers(self, event_type_name, event_source_uri):
        """
        Returns a list of handlers for parsed events of specified type
        and source. When no explicit handlers are registered and the class
        contains a custom implementation of the _parsed_event method, this
        method will be used as fallback handler for all parsed events.

        Args:
          event_type_name (str): The event type name
          event_source_uri (str): URI of the event source

        """
        handlers = self.__event_type_handlers.get(event_type_name, [])

        # Add handlers for the event source
        for pattern, source_handlers in self.__event_source_handlers.items():
            if event_source_uri in self.__source_uri_pattern_map[pattern]:
                handlers.extend(source_handlers)

        if len(handlers) == 0:
            # No handlers found, check if the empty
            # _parsed_event() method has been overridden
            # by a class extension, so we can use that
            # for handling events.
            this_method = getattr(type(self), '_parsed_event')
            base_method = getattr(EDXMLParserBase, '_parsed_event')
            if this_method != base_method:
                handlers = [self._parsed_event]

        return handlers

    def __parse_event(self, event):
        event_type_name = event.get_type_name()
        event_source_uri = event.get_source_uri()
        schema = self.get_event_type_schema(event_type_name)

        # TODO: To make things more efficient, we should keep lists of event types
        #       sources and validation schemas that we update whenever we receive
        #       and ontology element. That will make event parsing more lightweight.

        if self._ontology.get_event_source(event_source_uri) is None:
            raise EDXMLValidationError(
                "An input event refers to source URI %s, which is not defined." % event_source_uri
            )
        if self._ontology.get_event_type(event_type_name) is None:
            raise EDXMLValidationError(
                "An input event refers to event type %s, which is not defined." % event_type_name
            )

        if self.__validate and schema is not None:
            if not schema.validate(event):
                # Event does not validate. Try to generate a validation
                # exception that is more readable than the RelaxNG
                # error is, by validating using the EventType class.
                try:
                    self._ontology.get_event_type(event_type_name).validate_event_structure(event)

                    # EventType structure checks out alright. Let us check the object values.
                    self._ontology.get_event_type(event_type_name).validate_event_objects(event)

                    # EventType validation did not find the issue. We have
                    # no other option than to raise a RelaxNG error containing
                    # a undoubtedly cryptic error message.
                    raise EDXMLValidationError(str(schema.error_log))

                except EDXMLValidationError as exception:
                    schema = self._ontology.get_event_type(event_type_name).generate_relax_ng(self._ontology)
                    raise EDXMLValidationError(
                        'Event failed to validate:\n\n%s\nDetails:\n%s\n\nSchema:\n%s' % (
                            etree.tostring(event, pretty_print=True, encoding='unicode'), exception.args[0],
                            etree.tostring(schema, pretty_print=True, encoding='unicode'))
                    )

        # Call all event handlers in order
        for handler in self._get_event_handlers(event_type_name, event_source_uri):
            handler(event)

        self.__num_parsed_events += 1
        self.__num_parsed_event_types[event_type_name] += 1

    def _parsed_event(self, event):
        """

        Callback that is invoked for every event that is parsed
        from the input EDXML stream.

        Args:
          event (edxml.ParsedEvent): The parsed event

        """
        pass

    def _parse_foreign_element(self, element):
        """

        Callback that is invoked for foreign elements that are parsed
        from the input EDXML stream. While these elements are probably
        not EDXML events, they are still represented by ParsedEvent
        instances.

        Args:
          element (edxml.ParsedEvent): The parsed element

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

    def parse(self, input_file, foreign_element_tags=()):
        """

        Parses the specified file. The file can be any
        file-like object, or the name of a file that should
        be opened and parsed. The parser will generate calls
        to the various callback methods in the base class,
        allowing the parsed data to be processed.

        Optionally, a list of tags of foreign elements can be
        supplied. The tags must prepend the namespace in James
        Clark notation. Example:

        ['{http://some/foreign/namespace}attribute']

        These elements will be passed to the _parse_foreign_element() when encountered.

        Notes:
          Passing a file name rather than a file-like object
          is preferred and may result in a small performance gain.

        Args:
          input_file (Union[io.TextIOBase, file, str]):
          foreign_element_tags (List[str])

        Returns:
            edxml.EDXMLPullParser

        """

        self._element_iterator = etree.iterparse(
            input_file,
            events=['end'],
            tag=[
                '{http://edxml.org/edxml}edxml',
                '{http://edxml.org/edxml}ontology',
                '{http://edxml.org/edxml}event'
            ] + list(foreign_element_tags),
            no_network=True, resolve_entities=False, remove_comments=True, remove_pis=True
        )

        # Set a custom class that lxml should use for
        # representing event elements
        lookup = etree.ElementNamespaceClassLookup()
        if self._event_class is not None:
            lookup.get_namespace('http://edxml.org/edxml')['event'] = self._event_class
        else:
            lookup.get_namespace('http://edxml.org/edxml')['event'] = ParsedEvent
        self._element_iterator.set_element_class_lookup(lookup)

        try:
            self._parse_edxml()
        except XMLSyntaxError as e:
            raise EDXMLValidationError('Invalid XML: ' + str(e.error_log))

        return self


class EDXMLPushParser(EDXMLParserBase):
    """

    An incremental push parser for EDXML data. Unlike
    the pull parser, this parser does not read data
    by itself and does not block when the data stream
    dries up. It needs to be actively fed with stings,
    allowing full control of the input process.

    Optionally, a list of tags of foreign elements can be
    supplied. The tags must prepend the namespace in James
    Clark notation. Example:

    ['{http://some/foreign/namespace}attribute']

    These elements will be passed to the _parse_foreign_element() when encountered.

    Note:
      This class extends EDXMLParserBase, refer to that
      class for more details about the EDXML parsing interface.

    """

    def __init__(self, validate=True, foreign_element_tags=[]):
        super(EDXMLPushParser, self).__init__(validate)
        self.__foreign_element_tags = foreign_element_tags
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
                tag=[
                    '{http://edxml.org/edxml}edxml',
                    '{http://edxml.org/edxml}ontology',
                    '{http://edxml.org/edxml}event'
                ] + self.__foreign_element_tags,
                target=self.__feed_target, no_network=True, resolve_entities=False,
                remove_comments=True, remove_pis=True
            )

            # Set a custom class that lxml should use for
            # representing event elements
            lookup = etree.ElementNamespaceClassLookup()
            if self._event_class is not None:
                lookup.get_namespace('http://edxml.org/edxml')['event'] = self._event_class
            else:
                lookup.get_namespace('http://edxml.org/edxml')['event'] = ParsedEvent
            self.__inputParser.set_element_class_lookup(lookup)

            self._element_iterator = self.__inputParser.read_events()

        self.__inputParser.feed(data)

        try:
            self._parse_edxml()
        except XMLSyntaxError as e:
            raise EDXMLValidationError('Invalid XML: ' + str(e))

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
