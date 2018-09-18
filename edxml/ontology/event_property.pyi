# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any
from typing import Dict

from edxml.ontology import OntologyElement


class EventProperty(OntologyElement):

    EDXML_PROPERTY_NAME_PATTERN = ...

    MERGE_MATCH = ...
    """Merge strategy 'match'"""
    MERGE_DROP = ...
    """Merge strategy 'drop'"""
    MERGE_ADD = ...
    """Merge strategy 'add'"""
    MERGE_REPLACE = ...
    """Merge strategy 'replace'"""
    MERGE_MIN = ...
    """Merge strategy 'min'"""
    MERGE_MAX = ...
    """Merge strategy 'max'"""

    def __init__(self, event_type: edxml.ontology.EventType, name: str, object_type: edxml.ontology.ObjectType,
                 description: str = None, concept_name: str = None, concept_confidence: float = 0, cnp: int = 128,
                 unique: bool = False, optional: bool = False, multivalued: bool = True, merge: str = 'drop',
                 similar: str = '') -> None:

        self.__attr = ...       # type: Dict[str, Any]
        self.__event_type = ...  # type: edxml.ontology.EventType
        self.__object_type = ...  # type: edxml.ontology.ObjectType
        self.__data_type = ...  # type: edxml.ontology.DataType

    def _child_modified_callback(self) -> 'EventProperty': ...

    def _set_attr(self, key: str, value): ...

    def get_name(self) -> str: ...

    def get_description(self) -> str: ...

    def get_object_type_name(self) -> str: ...

    def get_merge_strategy(self) -> str: ...

    def get_concept_confidence(self) -> int: ...

    def get_concept_naming_priority(self) -> int: ...

    def get_similar_hint(self) -> str: ...

    def get_object_type(self) -> edxml.ontology.ObjectType: ...

    def get_data_type(self) -> edxml.ontology.DataType: ...

    def relate_to(self, type_predicate: str, target_property_name: str, reason: str = None, confidence: int = 10,
                  directed: bool = True) -> edxml.ontology.PropertyRelation: ...

    def relate_inter(self, type_predicate: str, target_property_name: str, reason: str = None, confidence: int = 10,
                     directed: bool = True) -> edxml.ontology.PropertyRelation: ...

    def relate_intra(self, type_predicate: str, target_property_name: str, reason: str = None, confidence: int = 10,
                     directed: bool = True) -> edxml.ontology.PropertyRelation: ...

    def set_merge_strategy(self, merge_strategy: str) -> 'EventProperty': ...

    def set_description(self, description: str) -> 'EventProperty': ...

    def unique(self) -> 'EventProperty': ...

    def is_unique(self) -> bool: ...

    def is_optional(self) -> bool: ...

    def is_mandatory(self) -> bool: ...

    def is_multi_valued(self) -> bool: ...

    def is_single_valued(self) -> bool: ...

    def identifies(self, concept_name: str, confidence: int) -> 'EventProperty': ...

    def set_multi_valued(self, is_multivalued:bool) -> 'EventProperty': ...

    def set_concept_naming_priority(self, priority: int) -> 'EventProperty': ...

    def get_concept_name(self) -> str: ...

    def hint_similar(self, similarity: str) -> 'EventProperty': ...

    def merge_add(self) -> 'EventProperty': ...

    def merge_replace(self) -> 'EventProperty': ...

    def merge_drop(self) -> 'EventProperty': ...

    def merge_min(self) -> 'EventProperty': ...

    def merge_max(self) -> 'EventProperty': ...

    def validate(self) -> 'EventProperty': ...

    @classmethod
    def create_from_xml(cls, property_element: etree.Element, ontology: edxml.ontology.Ontology,
                        parent_event_type: edxml.ontology.EventType) -> 'EventProperty': ...

    def update(self, event_property: 'EventProperty') -> 'EventProperty': ...

    def generate_xml(self) -> etree.Element: ...
