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
import edxml

from collections import defaultdict
from copy import deepcopy
from lxml import etree
from typing import Any
from typing import Dict
from typing import List
from EDXMLBase import *
from edxml import ParsedEvent


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
    self._elementIterator = None         # type: etree.Element
    self._eventClass = None

    self.__currentEventType = None       # type: str
    self.__currentEventSourceUri = None  # type: str
    self.__currentEventSource = None     # type: edxml.ontology.EventSource
    self.__currentGroupEventCount = 0    # type: int
    self.__rootElement = None            # type: etree.Element
    self.__currentGroupElement = None    # type: etree.Element
    self.__eventGroupsElement = None     # type: etree.Element
    self.__previousRootLength = None
    self.__numParsedEvents = 0           # type: int
    self.__numParsedEventTypes = {}      # type: Dict[str, int]
    self.__eventTypeHandlers = {}        # type: Dict[str, callable]
    self.__eventSourceHandlers = {}      # type: Dict[str, callable]
    self.__currentEventHandlers = []     # type: List[callable]
    self.__sourceUriPatternMap = {}      # type: Dict[Any, List[str]]

    self.__schema = None                 # type: etree.RelaxNG
    self.__eventTypeSchemaCache = {}     # type: Dict[str, etree.RelaxNG]
    self.__eventTypeSchema = None        # type: etree.RelaxNG

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
      self.__validateRootElement()
      self._close()

  def _close(self):
    """

    Callback that is invoked when the parsing process is
    finished or interrupted.

    Returns:
      EDXMLParserBase: The EDXML parser

    """
    return self

  def setEventTypeHandler(self, eventTypes, handler):
    """

    Register a handler for specified event types. Whenever
    an event is parsed of any of the specified types, the
    supplied handler will be called with the event (which
    will be a ParsedEvent instance) as its only argument.

    Multiple handlers can be installed for a given type of
    event, they will be invoked in the order of registration.
    Event type handlers are invoked before event source handlers.

    Args:
      eventTypes (List[str]): List of event type names
      handler (callable): Handler

    Returns:
      EDXMLParserBase: The EDXML parser

    """
    for eventType in eventTypes:
      if eventType not in self.__eventTypeHandlers:
        self.__eventTypeHandlers[eventType] = []
      self.__eventTypeHandlers[eventType].append(handler)

    return self

  def setEventSourceHandler(self, eventSourcePatterns, handler):
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
      eventSourcePatterns (List[str]): List of regular expressions
      handler (callable): Handler

    Returns:
      EDXMLParserBase: The EDXML parser

    """
    for pattern in eventSourcePatterns:
      if pattern not in self.__eventSourceHandlers:
        self.__eventSourceHandlers[pattern] = []
      self.__eventSourceHandlers[pattern].append(handler)

    return self

  def setCustomEventClass(self, eventClass):
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
      eventClass (etree.ElementBase): The custom element class

    Returns:
      EDXMLParserBase: The EDXML parser

    """
    self._eventClass = eventClass
    return self

  def getEventCounter(self):
    """

    Returns the number of parsed events. This counter
    is incremented after the _parsedEvent callback returned.

    Returns:
      int: The number of parsed events
    """
    return self.__numParsedEvents

  def getEventTypeCounter(self, eventTypeName):
    """

    Returns the number of parsed events of the specified
    event type. These counters are incremented after the
    _parsedEvent callback returned.

    Args:
      eventTypeName (str): The type of parsed events

    Returns:
      int: The number of parsed events
    """
    return self.__numParsedEventTypes.get(eventTypeName, 0)

  def getOntology(self):
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

  def getEventTypeSchema(self, eventTypeName):
    """

    Returns the RelaxNG schema that is used by the parser
    to validate the specified event type. Returns None if
    the event type is not known to the parser.

    Args:
      eventTypeName (str):

    Returns:
      etree.RelaxNG:
    """
    if eventTypeName not in self.__eventTypeSchemaCache:
      self.__eventTypeSchemaCache[eventTypeName] = etree.RelaxNG(
        self._ontology.GetEventType(eventTypeName).generateRelaxNG(self._ontology)
      )
    return self.__eventTypeSchemaCache.get(eventTypeName)

  def __findRootElement(self, eventElement):
    # Find the root element by traversing up the
    # tree. The first parent element that we will
    # find this way is the eventgroup tag that
    # contains the current event.
    self.__rootElement = eventElement.getparent()
    while self.__rootElement is not None and self.__rootElement.tag != 'edxml':
      self.__rootElement = self.__rootElement.getparent()
    if self.__rootElement is None or self.__rootElement.tag != 'edxml':
      raise EDXMLValidationError('Invalid EDXML structure detected: Could not find the edxml root tag.')

  def __validateRootElement(self):
    # Note that this method can only be called after
    # parsing is completed. At any other stage in the
    # parsing process, the tree structure is incomplete.
    if not self.__schema:
      self.__schema = etree.RelaxNG(
        etree.parse(os.path.dirname(os.path.realpath(__file__)) + '/schema/edxml-schema-3.0.0.rng')
      )

    try:
      self.__schema.assertValid(self.__rootElement)
    except (etree.DocumentInvalid, etree.XMLSyntaxError) as ValidationError:
      # XML structure is invalid.
      raise EDXMLValidationError(
        "Invalid EDXML structure detected: %s\nThe RelaxNG validator generated the following error: %s" %
        (etree.tostring(self.__rootElement), str(ValidationError))
      )

  def __validateDefinitionsElement(self, ontologyElement):
    if not self.__schema:
      self.__schema = etree.RelaxNG(
        etree.parse(os.path.dirname(os.path.realpath(__file__)) + '/schema/edxml-schema-3.0.0.rng')
      )

    # Since lxml iterparse gives us partial XML
    # trees, elements from which we have not seen
    # its closing tag yet may not be valid yet. So,
    # we integrate the ontology element into a
    # skeleton tree, yielding a complete, valid
    # EDXML structure.
    skeleton = etree.Element('edxml', attrib=self.__rootElement.attrib)
    skeleton.append(deepcopy(ontologyElement))
    etree.SubElement(skeleton, 'eventgroups')

    try:
      self.__schema.assertValid(skeleton)
    except (etree.DocumentInvalid, etree.XMLSyntaxError) as ValidationError:
      # XML structure is invalid.
      raise EDXMLValidationError(
        "Invalid EDXML structure detected: %s\nThe RelaxNG validator generated the following error: %s" %
        (etree.tostring(self.__rootElement), str(ValidationError))
      )

  def __processOntology(self, ontologyElement):
    precedingEventGroupsElement = ontologyElement.getprevious()
    if precedingEventGroupsElement is not None:
      precedingDefinitionsElement = precedingEventGroupsElement.getprevious()
      if precedingDefinitionsElement is None:
        # XML structure is invalid, because there must be
        # an ontology element preceding the eventgroups element.
        raise EDXMLValidationError(
          "EDXML structure contains an ontology element without a preceding eventgroups element: %s\n" %
          (etree.tostring(self.__rootElement))
        )

      # We have one complete pair of an ontology and
      # an eventgroups element preceding the current ontology
      # element. We can safely delete them.
      del self.__rootElement[0:2]

    # Before parsing the ontology information, we validate
    # the generic structure of the ontology element, using
    # the RelaxNG schema.
    self.__validateDefinitionsElement(ontologyElement)

    # We survived XML structure validation. We can proceed
    # and process the new ontology information.
    if self._ontology is None:
      self._ontology = edxml.ontology.Ontology()

    try:
      self._ontology.Update(ontologyElement)
      self.__eventTypeSchemaCache = {}
    except EDXMLValidationError as exception:
      exception.message = "Invalid ontology definition detected: %s\n%s" %\
                          (etree.tostring(ontologyElement, pretty_print=True), exception.message)
      raise

    for eventTypeName in self._ontology.GetEventTypeNames():
      self.__numParsedEventTypes[eventTypeName] = 0

    # Invoke callback to inform about the
    # new ontology.
    self._parsedOntology(self._ontology)

    # Use the ontology to build a mapping of event
    # handler source patterns to source URIs
    self.__sourceUriPatternMap = defaultdict(list)
    for pattern in self.__eventSourceHandlers.keys():
      for sourceUri, source in self._ontology.GetEventSources():
        if re.match(pattern, sourceUri):
          self.__sourceUriPatternMap[pattern].append(sourceUri)

  def _parsedOntology(self, edxmlOntology):
    """
    Callback that is invoked when the ontology has
    been updated from input data. The passed ontology
    contains the result of merging all ontology information
    that has been parsed so far.

    Args:
      edxmlOntology (edxml.ontology.Ontology): The parsed ontology
    """
    # Since an override of this method may call this parent
    # method passing a different ontology, we assign it here.
    self._ontology = edxmlOntology

  def _parseEdxml(self):

    for action, elem in self._elementIterator:

      if self.__rootElement is None:
        self.__findRootElement(elem)

      if elem.tag == 'edxml':
        if elem.getparent() is None:
          versionString = elem.attrib['version']
          if versionString is None:
            raise EDXMLValidationError('Root element is missing the version attribute.')
          version = versionString.split('.')
          if len(version) != 3:
            raise EDXMLValidationError('Root element contains invalid version attribute: "%s"' % versionString)
          if int(version[0]) != 3 or int(version[1]) > 0:
            raise EDXMLValidationError('Unsupported EDXML version: "%s"' % versionString)
        continue

      if elem.tag == 'event':
        if elem.getparent().tag == 'eventgroup':
          if self.__currentGroupElement is None:
            # Apparently, we did not parse the current event group
            # yet.
            self.__parseEventGroup(elem.getparent())

          if self.__currentEventType is not None and self.__currentEventSourceUri is not None:
            elem.SetType(self.__currentEventType).SetSource(self.__currentEventSourceUri)
            self.__parseEvent(elem)
            self.__currentGroupEventCount += 1
            if self.__currentGroupEventCount > 1:
              # Delete the event tag, unless it is
              # the first event tag in the event group.
              # We do not want to delete the event that
              # we are currently processing, lxml does
              # not like that.
              del self.__currentGroupElement[0]
              pass
        continue

      if elem.tag == 'eventgroup':
        if elem.getparent().tag == 'eventgroups':
          if self.__currentGroupElement is not None:
            self._closeEventGroup(self.__currentEventType, self.__currentEventSourceUri)
            self.__currentGroupEventCount = 0
          self.__currentGroupElement = None
          self.__currentEventType = None
          self.__currentEventSource = None
          self.__currentEventSourceUri = None
        continue

      if elem.tag == 'ontology':
        if elem.getparent().tag == 'edxml':
          self.__processOntology(elem)
        continue

  def __parseEventGroup(self, groupElement):

    if self.__currentGroupElement is not None:
      self._closeEventGroup(self.__currentEventType, self.__currentEventSourceUri)

    # Since lxml iterparse gives us partial XML
    # trees, elements from which we have not seen
    # its closing tag yet may not be valid yet. For
    # that reason, we cannot use the EDXML RelaxNG
    # schema to validate the full XML structure while
    # parsing is still in progress. Hence the explicit
    # attribute validation here.

    eventTypeName = groupElement.attrib.get('event-type', '')
    sourceUri = groupElement.attrib.get('source-uri', '')
    if not re.match(edxml.ontology.EventType.NAME_PATTERN.pattern, eventTypeName):
      raise EDXMLValidationError('An eventgroup tag has an invalid event-type attribute: "%s"' % eventTypeName)
    if not re.match(edxml.ontology.EventSource.SOURCE_URI_PATTERN.pattern, sourceUri):
      raise EDXMLValidationError('An eventgroup tag has an invalid source-uri attribute: "%s"' % sourceUri)

    self.__currentGroupElement = groupElement
    self._openEventGroup(groupElement.attrib['event-type'], groupElement.attrib['source-uri'])

    if self.__currentEventType is None and self.__currentEventSourceUri is None:
      # This may happen when an extension of this
      # class 'swallows' an event group.
      self.__currentEventSource = None
      self.__currentEventSourceUri = None
      self.__eventTypeSchema = None
      return

    self.__currentEventSource = self._ontology.GetEventSource(self.__currentEventSourceUri)

    if self.__currentEventSource is None:
      raise EDXMLValidationError(
        "An eventgroup refers to Source URI %s, which is not defined." % self.__currentEventSourceUri
      )
    if self._ontology.GetEventType(self.__currentEventType) is None:
      raise EDXMLValidationError(
        "An eventgroup refers to eventtype %s, which is not defined." % self.__currentEventType
      )

    self.__currentEventSourceUri = self.__currentEventSource.GetUri()

    if self.__validate:
      self.__eventTypeSchema = self.getEventTypeSchema(self.__currentEventType)

  def _closeEventGroup(self, eventTypeName, eventSourceUri):
    """

    Callback that is invoked whenever an open event group
    is closed. The event type name and source URI match the
    values that were passed to _openEventGroup().

    Args:
      eventTypeName (str): The event type name
      eventSourceUri (str): URI of the event source

    """
    pass

  def _openEventGroup(self, eventTypeName, eventSourceUri):
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
    the group is parsed, the _closeEventGroup callback is
    invoked normally.

    Args:
      eventTypeName (str): The event type name
      eventSourceUri (str): URI of the event source

    """
    self.__currentEventType = eventTypeName
    self.__currentEventSourceUri = eventSourceUri

    self.__currentEventHandlers = []

    if self.__currentEventType and self.__currentEventSourceUri:

      # Add handlers for the event type
      self.__currentEventHandlers.extend(self.__eventTypeHandlers.get(self.__currentEventType, ()))

      # Add handlers for the event source
      for pattern, handlers in self.__eventSourceHandlers.iteritems():
        if self.__currentEventSourceUri in self.__sourceUriPatternMap[pattern]:
          self.__currentEventHandlers.extend(handlers)

    if len(self.__currentEventHandlers) == 0:
      # No handlers found, check if the empty
      # _parsedEvent() method has been overridden
      # by a class extension, so we can use that
      # for handling events.
      thisMethod = getattr(self, '_parsedEvent')
      baseMethod = getattr(EDXMLParserBase, '_parsedEvent')
      if thisMethod.__func__ is not baseMethod.__func__:
        self.__currentEventHandlers.append(self._parsedEvent)

  def __parseEvent(self, event):
    if self.__validate and self.__eventTypeSchema is not None:
      if not self.__eventTypeSchema.validate(event):
        # Event does not validate. Try to generate a validation
        # exception that is more readable than the RelaxNG
        # error is, by validating using the EventType class.
        try:
          self._ontology.GetEventType(self.__currentEventType).validateEventStructure(event)

          # EventType structure checks out alright. Let us check the object values.
          self._ontology.GetEventType(self.__currentEventType).validateEventObjects(event)

          # EventType validation did not find the issue. We have
          # no other option than to raise a RelaxNG error containing
          # a undoubtedly cryptic error message.
          raise EDXMLValidationError(self.__eventTypeSchema.error_log)

        except EDXMLValidationError as exception:
          schema = self._ontology.GetEventType(self.__currentEventType).generateRelaxNG(self._ontology)
          raise EDXMLValidationError, 'Event failed to validate:\n%s\n\n%s\nSchema:\n%s' % (
            etree.tostring(event, pretty_print=True).encode('utf-8'), exception,
            etree.tostring(schema, pretty_print=True)), sys.exc_info()[2]

    # Call all event handlers in order
    for handler in self.__currentEventHandlers:
      handler(event)

    self.__numParsedEvents += 1
    if self.__currentEventType:
      self.__numParsedEventTypes[self.__currentEventType] += 1

  def _parsedEvent(self, edxmlEvent):
    """

    Callback that is invoked for every event that is parsed
    from the input EDXML stream.

    Args:
      edxmlEvent (edxml.ParsedEvent): The parsed event

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

  def parse(self, inputFile):
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
      inputFile (Union[io.TextIOBase, file, str]):

    """
    self._elementIterator = etree.iterparse(
      inputFile,
      events=['end'],
      tag=('edxml', 'ontology', 'eventgroup', 'event'),
      no_network=True, resolve_entities=False
    )

    # Set a custom class that lxml should use for
    # representing event elements
    lookup = etree.ElementNamespaceClassLookup()
    if self._eventClass is not None:
      lookup.get_namespace('')['event'] = self._eventClass
    else:
      lookup.get_namespace('')['event'] = ParsedEvent
    self._elementIterator.set_element_class_lookup(lookup)
    self._parseEdxml()


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
    self.__feedTarget = None

  def feed(self, data):
    """

    Feeds the specified string to the parser. A call
    to the feed() method may or may not trigger calls
    to callback methods, depending on the size and
    content of the passed string buffer.

    Args:
      data (str): String data

    """
    if self._elementIterator is None:
      self.__inputParser = etree.XMLPullParser(
        events=['end'],
        tag=('event', 'eventgroup', 'ontology'),
        target=self.__feedTarget, no_network=True, resolve_entities=False
      )

      # Set a custom class that lxml should use for
      # representing event elements
      lookup = etree.ElementNamespaceClassLookup()
      if self._eventClass is not None:
        lookup.get_namespace('')['event'] = self._eventClass
      else:
        lookup.get_namespace('')['event'] = ParsedEvent
      self.__inputParser.set_element_class_lookup(lookup)

      self._elementIterator = self.__inputParser.read_events()
    self.__inputParser.feed(data)
    self._parseEdxml()

  def setFeedTarget(self, target):
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
    self.__feedTarget = target
    return self


class EDXMLOntologyPullParser(EDXMLPullParser):
  """
  A variant of the incremental pull parser which interrupts
  the parsing process when the ontology has been read. It does
  so by raising EDXMLOntologyPullParser.ProcessingInterrupted.
  It can be used to extract ontology information from EDXML
  data streams and skip reading the event data.
  """

  # TODO: When we get multiple ontology sections in the input,
  # override the parse method to skip all event tags and offer
  # an option to scan the full data stream for ontology info.

  class ProcessingInterrupted(Exception):
    pass

  def _parsedOntology(self, edxmlOntology):
    super(EDXMLOntologyPullParser, self)._parsedOntology(edxmlOntology)
    raise EDXMLOntologyPullParser.ProcessingInterrupted


class EDXMLOntologyPushParser(EDXMLPushParser):
  """
  A variant of the incremental push parser which interrupts
  the parsing process when the ontology has been read. It does
  so by raising EDXMLOntologyPushParser.ProcessingInterrupted.
  It can be used to extract ontology information from EDXML
  data streams and skip reading the event data.
  """

  # TODO: When we get multiple ontology sections in the input,
  # override the parse method to skip all event tags and offer
  # an option to scan the full data stream for ontology info.

  class ProcessingInterrupted(Exception):
    pass

  def _parsedOntology(self, edxmlOntology):
    super(EDXMLOntologyPushParser, self)._parsedOntology(edxmlOntology)
    raise EDXMLOntologyPushParser.ProcessingInterrupted
