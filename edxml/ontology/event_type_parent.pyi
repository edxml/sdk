# -*- coding: utf-8 -*-
import edxml
from lxml import etree
from typing import Dict

from edxml.ontology import OntologyElement


class EventTypeParent(OntologyElement):

    PROPERTY_MAP_PATTERN = ...

    def __init__(self, child_event_type: edxml.ontology.EventType, parent_event_type_name: str, property_map: str,
                 parent_description: str = None, siblings_description: str = None) -> None:

        self._attr = ...
        self._child_event_type = ...  # type: edxml.ontology.EventType

    @classmethod
    def create(cls, child_event_type: edxml.ontology.EventType, parent_event_type_name: str,
               property_map: Dict[str, str], parent_description: str = None,
               siblings_description: str = None) -> 'EventTypeParent': ...

    def _child_modified_callback(self) -> 'EventTypeParent': ...

    def _set_attr(self, key: str, value): ...

    def set_parent_description(self, description: str) -> 'EventTypeParent': ...

    def set_siblings_description(self, description: str) -> 'EventTypeParent': ...

    def map(self, child_property_name: str, parent_property_name: str = None) -> 'EventTypeParent': ...

    def get_event_type_name(self) -> str: ...

    def get_property_map(self) -> Dict[str, str]: ...

    def get_parent_description(self) -> str: ...

    def get_siblings_description(self) -> str: ...

    def validate(self) -> 'EventTypeParent': ...

    @classmethod
    def create_from_xml(cls, parent_element: etree.Element, child_event_type: edxml.ontology.EventType) -> 'EventTypeParent': ...

    def update(self, parent: 'EventTypeParent') -> 'EventTypeParent': ...

    def generate_xml(self) -> etree.Element: ...
