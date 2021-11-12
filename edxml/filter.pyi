# -*- coding: utf-8 -*-
from edxml import EDXMLWriter, ParsedEvent
from edxml.ontology import Ontology
from edxml.parser import EDXMLParserBase, EDXMLPullParser, EDXMLPushParser


class EDXMLFilterBase(EDXMLParserBase):

    def __init__(self, output, validate=True) -> None:

        self._writer = ...      # type: EDXMLWriter
        self.__groupOpen = ...  # type: bool

    def _parsed_ontology(self, parsed_ontology: Ontology) -> None: ...

    def _parsed_event(self, event: ParsedEvent) -> None: ...


class EDXMLPullFilter(EDXMLPullParser, EDXMLFilterBase):
    ...

class EDXMLPushFilter(EDXMLPushParser, EDXMLFilterBase):
    ...
