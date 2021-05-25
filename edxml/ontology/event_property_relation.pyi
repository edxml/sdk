# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any, Optional, Set
from typing import Dict

from edxml.ontology import OntologyElement


class PropertyRelation(OntologyElement):

    def __init__(self, event_type: edxml.ontology.EventType, source: edxml.ontology.EventProperty,
                 target: edxml.ontology.EventProperty, source_concept: edxml.ontology.Concept,
                 target_concept: edxml.ontology.Concept, description: Optional[str], type_class: str,
                 type_predicate: Optional[str], confidence: Optional[float] = 10) -> None:

        self._type = ...         # type: str
        self.__attr = ...      # type: Dict[str, Any]
        self.__event_type = ...  # type: edxml.ontology.EventType

    def _child_modified_callback(self) -> 'PropertyRelation': ...

    def _set_attr(self, key: str, value): ...

    def is_reversed(self) -> bool: ...

    def get_persistent_id(self) -> str: ...

    def get_source(self) -> str: ...

    def get_target(self) -> str: ...

    def get_source_concept(self) -> str: ...

    def get_target_concept(self) -> str: ...

    def get_description(self) -> str: ...

    def get_type(self) -> str: ...

    def get_predicate(self) -> str: ...

    def get_confidence(self) -> int: ...

    def evaluate_description(self, event_properties: Dict[str, Set],
                             capitalize=True, colorize=False, ignore_value_errors=False) -> str: ...

    def because(self, reason: str) -> 'PropertyRelation': ...

    def set_description(self, description: Optional[str]) -> 'PropertyRelation': ...

    def set_predicate(self, predicate: Optional[str]) -> 'PropertyRelation': ...

    def set_confidence(self, confidence: Optional[int]): ...

    def validate(self) -> 'PropertyRelation': ...

    @classmethod
    def create_from_xml(cls, relation_element: etree.Element,
                        event_type: edxml.ontology.EventType,
                        ontology: edxml.ontology.Ontology) -> 'PropertyRelation': ...

    def update(self, property_relation: 'PropertyRelation') -> 'PropertyRelation': ...

    def generate_xml(self) -> etree.Element: ...

    def reversed(self) -> 'PropertyRelation': ...
