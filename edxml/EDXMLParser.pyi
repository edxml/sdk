# -*- coding: utf-8 -*-
import io

from lxml import etree
from typing import Union, List

import edxml


class EDXMLParserBase(object):

  def __init__(self, validate: bool=True) -> None:
    super(EDXMLParserBase, self).__init__()

    self._ontology = ...                # type: edxml.ontology.Ontology
    self._elementIterator = ...         # type: etree.Element
    self._eventClass = ...

  def _close(self) -> 'EDXMLParserBase': ...

  def setEventTypeHandler(self, eventTypes: List[str], handler: callable) -> 'EDXMLParserBase': ...

  def setEventSourceHandler(self, eventSourcePatterns: List[str], handler: callable) -> 'EDXMLParserBase': ...

  def setCustomEventClass(self, eventClass: etree.ElementBase) -> 'EDXMLParserBase': ...

  def getEventCounter(self) -> int: ...

  def getEventTypeCounter(self, eventTypeName) -> int: ...

  def getOntology(self) -> edxml.ontology.Ontology: ...

  def getEventTypeSchema(self, eventTypeName: str) -> etree.RelaxNG: ...

  def _findRootElement(self, eventElement: etree.Element) -> None: ...

  def _validateXmlTree(self) -> None: ...

  def _processOntology(self, ontologyElement: etree.Element) -> None: ...

  def _parsedOntology(self, edxmlOntology: edxml.ontology.Ontology) -> None: ...

  def _parseEdxml(self) -> None: ...

  def _parseEventGroup(self, groupElement: etree.Element) -> None: ...

  def _closeEventGroup(self, eventTypeName: str, eventSourceId: str) -> None: ...

  def _openEventGroup(self, eventTypeName: str, eventSourceId: str) -> None: ...

  def _parsedEvent(self, edxmlEvent: edxml.ParsedEvent) -> None: ...


class EDXMLPullParser(EDXMLParserBase):

  def parse(self, inputFile: Union[io.TextIOBase, file, str]) -> 'EDXMLPullParser': ...

  def _parsedOntology(self, edxmlOntology: edxml.ontology.Ontology) -> None: ...

  def _parsedEvent(self, edxmlEvent: edxml.ParsedEvent) -> None: ...


class EDXMLPushParser(EDXMLParserBase):

  #def __init__(self, validate: bool = True) -> None: ...
    # super(EDXMLPushParser).__init__(validate)
    # self._inputParser = ... # type: etree.XMLPullParser
    # self._feedTarget = ... # type: object

  def feed(self, data: str) -> None: ...

  def setFeedTarget(self, target: object) -> 'EDXMLParserBase': ...

  def _parsedEvent(self, edxmlEvent: edxml.ParsedEvent) -> None: ...

class EDXMLOntologyPullParser(EDXMLPullParser): ...

class EDXMLOntologyPushParser(EDXMLPushParser): ...