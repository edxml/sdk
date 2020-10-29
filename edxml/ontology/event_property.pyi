# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any, Optional, Callable
from typing import Dict

from edxml.ontology import OntologyElement, PropertyConcept


class EventProperty(OntologyElement):

    EDXML_PROPERTY_NAME_PATTERN = ...

    MERGE_MATCH = ...
    """Merge strategy 'match'"""
    MERGE_DROP = ...
    """Merge strategy 'drop'"""
    MERGE_ADD = ...
    """Merge strategy 'add'"""
    MERGE_SET = 'set'
    """Merge strategy 'set'"""
    MERGE_REPLACE = ...
    """Merge strategy 'replace'"""
    MERGE_MIN = ...
    """Merge strategy 'min'"""
    MERGE_MAX = ...
    """Merge strategy 'max'"""

    def __init__(self, event_type: edxml.ontology.EventType, name: str, object_type: edxml.ontology.ObjectType,
                 description: str = None, optional: bool = False, multivalued: bool = True, merge: str = 'drop',
                 similar: str = '', confidence: int = 10) -> None:

        self.__attr = ...       # type: Dict[str, Any]
        self.__event_type = ...  # type: edxml.ontology.EventType
        self.__object_type = ...  # type: edxml.ontology.ObjectType
        self.__data_type = ...  # type: edxml.ontology.DataType
        self.__concepts = ...  # type: Dict[str, edxml.ontology.PropertyConcept]

    def _child_modified_callback(self) -> 'EventProperty': ...

    def _set_attr(self, key: str, value): ...

    def __getattr__(self, relation_type_predicate: str) -> \
            Callable[[str, Optional[str], Optional[int], Optional[bool]], edxml.ontology.PropertyRelation] : ...

    def _validate_attributes(self) -> None: ...

    def _validate_merge_strategy(self) -> None: ...

    def get_name(self) -> str: ...

    def get_description(self) -> str: ...

    def get_object_type_name(self) -> str: ...

    def get_merge_strategy(self) -> str: ...

    def get_concept_confidence(self) -> int: ...

    def get_concept_naming_priority(self) -> int: ...

    def get_similar_hint(self) -> str: ...

    def get_confidence(self) -> int: ...

    def get_object_type(self) -> edxml.ontology.ObjectType: ...

    def get_data_type(self) -> edxml.ontology.DataType: ...

    def get_concept_associations(self) -> Dict[str,edxml.ontology.PropertyConcept]: ...

    def relate_to(self, type_predicate: str, target_property_name: str, reason: str = None, confidence: int = 10,
                  directed: bool = True) -> edxml.ontology.PropertyRelation: ...

    def relate_inter(self, type_predicate: str, target_property_name: str, source_concept_name=None,
                     target_concept_name=None, reason: str = None, confidence: int = 10,
                     directed: bool = True) -> edxml.ontology.PropertyRelation: ...

    def relate_intra(self, type_predicate: str, target_property_name: str, source_concept_name=None,
                     target_concept_name=None, reason: str = None, confidence: int = 10,
                     directed: bool = True) -> edxml.ontology.PropertyRelation: ...

    def add_associated_concept(self, concept_association: PropertyConcept) -> 'EventProperty': ...

    def set_merge_strategy(self, merge_strategy: str) -> 'EventProperty': ...

    def set_description(self, description: str) -> 'EventProperty': ...

    def set_confidence(self, confidence: int) -> 'EventProperty': ...

    def make_optional(self) -> 'EventProperty': ...

    def make_mandatory(self) -> 'EventProperty': ...

    def set_optional(self, is_optional: bool) -> 'EventProperty': ...

    def make_multivalued(self) -> 'EventProperty': ...

    def make_hashed(self) -> 'EventProperty': ...

    def is_hashed(self) -> bool: ...

    def is_optional(self) -> bool: ...

    def is_mandatory(self) -> bool: ...

    def is_multi_valued(self) -> bool: ...

    def is_single_valued(self) -> bool: ...

    def identifies(self, concept_name: str, confidence: int = 10, cnp: int = 128) -> PropertyConcept: ...

    def set_multi_valued(self, is_multivalued:bool) -> 'EventProperty': ...

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
