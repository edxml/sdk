# -*- coding: utf-8 -*-

import edxml

from datetime import datetime
from lxml import etree
from typing import Any
from typing import Dict


class EventSource(object):

    SOURCE_URI_PATTERN = ...
    ACQUISITION_DATE_PATTERN = ...

    def __init__(self, ontology: edxml.ontology.Ontology, uri: str, description: str = 'no description available',
                 acquisition_date: str = '00000000') -> None:

        self._attr = ...     # type: Dict[str, Any]
        self._ontology = ...  # type: edxml.ontology.Ontology

    def _child_modified_callback(self) -> 'EventSource': ...

    def _set_attr(self, key: str, value): ...

    def get_uri(self) -> str: ...

    def get_acquisition_date_string(self) -> str: ...

    def get_description(self) -> str: ...

    def set_description(self, description: str) -> 'EventSource': ...

    def set_acquisition_date(self, date_time: datetime): ...

    def validate(self) -> 'EventSource': ...

    @classmethod
    def create_from_xml(cls, source_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'EventSource': ...

    def update(self, source: 'EventSource') -> 'EventSource': ...

    def generate_xml(self) -> etree.Element: ...
