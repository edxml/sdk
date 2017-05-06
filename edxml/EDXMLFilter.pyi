# -*- coding: utf-8 -*-
import edxml
from edxml.EDXMLParser import EDXMLParserBase, EDXMLPullParser, EDXMLPushParser


class EDXMLFilter(EDXMLParserBase):

  def __init__(self) -> None:

    self._writer = ...     # type: edxml.EDXMLWriter
    self.__groupOpen = ... # type: bool

  def _parsedOntology(self, parsedOntology: edxml.ontology.Ontology) -> None: ...

  def _parsedEvent(self, edxmlEvent: edxml.ParsedEvent) -> None: ...

class EDXMLPullFilter(EDXMLPullParser, EDXMLFilter):

  def __init__(self, Output, Validate=True):

    self._writer = ...     # type: edxml.EDXMLWriter

  def _parsedEvent(self, event: edxml.ParsedEvent) -> None: ...


class EDXMLPushFilter(EDXMLPushParser, EDXMLFilter):

  def __init__(self, Output, Validate=True):

    self._writer = ...     # type: edxml.EDXMLWriter

  def _parsedEvent(self, event: edxml.ParsedEvent) -> None: ...
