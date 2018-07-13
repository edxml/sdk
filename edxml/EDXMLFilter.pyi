# -*- coding: utf-8 -*-
import edxml
from edxml.EDXMLParser import EDXMLParserBase, EDXMLPullParser, EDXMLPushParser


class EDXMLFilter(EDXMLParserBase):

    def __init__(self) -> None:

        self._writer = ...      # type: edxml.EDXMLWriter
        self.__groupOpen = ...  # type: bool

    def _parsed_ontology(self, parsed_ontology: edxml.ontology.Ontology) -> None: ...

    def _parsed_event(self, event: edxml.ParsedEvent) -> None: ...


class EDXMLPullFilter(EDXMLPullParser, EDXMLFilter):

    def __init__(self, output, validate=True):

        self._writer = ...     # type: edxml.EDXMLWriter

    def _parsed_event(self, event: edxml.ParsedEvent) -> None: ...


class EDXMLPushFilter(EDXMLPushParser, EDXMLFilter):

    def __init__(self, output, validate=True):

        self._writer = ...     # type: edxml.EDXMLWriter

    def _parsed_event(self, event: edxml.ParsedEvent) -> None: ...
