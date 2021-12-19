# -*- coding: utf-8 -*-
from edxml import EDXMLWriter, ParsedEvent
from edxml.ontology import Ontology
from edxml.parser import EDXMLParserBase, EDXMLPullParser, EDXMLPushParser


class EDXMLFilterBase(EDXMLParserBase):

    def __init__(self, output, validate=True) -> None:

        self._writer = ...      # type: EDXMLWriter

    def _parsed_ontology(self, parsed_ontology: Ontology, filtered_ontology: Ontology=None) -> None: ...

    def _parsed_event(self, event: ParsedEvent) -> None: ...


class EDXMLPullFilter(EDXMLPullParser, EDXMLFilterBase):
    def __init__(self, output, validate=True) -> None: ...

class EDXMLPushFilter(EDXMLPushParser, EDXMLFilterBase):
    def __init__(self, output, validate=True) -> None: ...
