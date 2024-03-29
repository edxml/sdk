# -*- coding: utf-8 -*-

import edxml

from datetime import datetime
from lxml import etree
from typing import Any, Optional
from typing import Dict

from edxml.ontology import OntologyElement


class EventSource(OntologyElement):

    SOURCE_URI_PATTERN = ...
    ACQUISITION_DATE_PATTERN = ...

    def __init__(self, ontology: edxml.ontology.Ontology, uri: str, description: str = 'no description available',
                 acquisition_date: str = None) -> None:

        self._attr = ...     # type: Dict[str, Any]
        self._ontology = ...  # type: edxml.ontology.Ontology

    def _child_modified_callback(self) -> 'EventSource': ...

    def _set_attr(self, key: str, value): ...

    def get_uri(self) -> str: ...

    def get_acquisition_date(self) -> Optional[datetime]: ...

    def get_acquisition_date_string(self) -> Optional[str]: ...

    def get_description(self) -> str: ...

    def get_version(self) -> int: ...

    def set_description(self, description: str) -> 'EventSource': ...

    def set_acquisition_date(self, date_time: datetime) -> 'EventSource': ...

    def set_acquisition_date_string(self, date_time: str) -> 'EventSource': ...

    def set_version(self, version: int) -> 'EventSource': ...

    def validate(self) -> 'EventSource': ...

    @classmethod
    def create_from_xml(cls, source_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'EventSource': ...

    def update(self, source: 'EventSource') -> 'EventSource': ...

    def generate_xml(self) -> etree.Element: ...
