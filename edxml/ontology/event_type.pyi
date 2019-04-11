# -*- coding: utf-8 -*-
import edxml

from typing import List, Dict, Iterable
from lxml import etree

from edxml.ontology import OntologyElement


class EventType(OntologyElement):

    NAME_PATTERN = ...
    DISPLAY_NAME_PATTERN = ...
    CLASS_LIST_PATTERN = ...
    TEMPLATE_PATTERN = ...
    KNOWN_FORMATTERS = ...  # type: List[str]

    def __init__(self, ontology: edxml.ontology.Ontology, name: str, display_name: str = None, description: str = None,
                 class_list: str = '', summary: str = 'no description available',
                 story: str = 'no description available', parent: edxml.ontology.EventTypeParent = None) -> None:

        self.__attr = ...              # type: Dict
        self.__properties = ...        # type: Dict[str, edxml.ontology.EventProperty]
        self.__relations = ...         # type: Dict[str, edxml.ontology.PropertyRelation]
        self.__parent = ...            # type: edxml.ontology.EventTypeParent
        self.__parent_description = ...  # type: str
        self.__relax_ng = None          # type: etree.RelaxNG
        self.__ontology = ...           # type: edxml.ontology.Ontology

        self.__cachedUniqueProperties = ...  # type: Dict[str, edxml.ontology.EventProperty]
        self.__cachedHashProperties = ...    # type: Dict[str, edxml.ontology.EventProperty]

    def __getitem__(self, property_name: str) -> edxml.ontology.EventProperty: ...

    def _child_modified_callback(self) -> 'EventType': ...

    def _set_attr(self, key: str, value): ...

    def get_name(self) -> str: ...

    def get_description(self) -> str: ...

    def get_display_name_singular(self) -> str: ...

    def get_display_name_plural(self) -> str: ...

    def get_classes(self) -> List[str]: ...

    def get_properties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def get_unique_properties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def get_hash_properties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def get_property_relations(self) -> Dict[str, edxml.ontology.PropertyRelation]: ...

    def get_version(self) -> int: ...

    def has_class(self, class_name) -> bool: ...

    def is_unique(self) -> bool: ...

    def get_summary_template(self) -> str: ...

    def get_story_template(self) -> str: ...

    def get_parent(self) -> edxml.ontology.EventTypeParent: ...

    def create_property(self, name: str, object_type_name: str, description: str = None) -> edxml.ontology.EventProperty: ...

    def add_property(self, property_name: edxml.ontology.EventProperty) -> 'EventType': ...

    def remove_property(self, property_name: str) -> 'EventType': ...

    def create_relation(
            self, source: str, target: str, description: str, type_class: str, type_predicate: str,
            source_concept_name=None, target_concept_name=None, confidence: float = 1.0, directed: bool = True
    ) -> edxml.ontology.PropertyRelation: ...

    def add_relation(self, relation: edxml.ontology.PropertyRelation) -> 'EventType': ...

    def make_children(self, siblings_description: str, parent: 'EventType') -> edxml.ontology.EventTypeParent: ...

    def is_parent(self, parent_description, child: 'EventType') -> 'EventType': ...

    def set_description(self, description: str) -> 'EventType': ...

    def set_parent(self, parent: edxml.ontology.EventTypeParent) -> 'EventType': ...

    def add_class(self, class_name: str) -> 'EventType': ...

    def set_classes(self, class_names: Iterable[str]) -> 'EventType': ...

    def set_name(self, event_type_name: str) -> 'EventType': ...

    def set_display_name(self, singular: str, plural: str = None) -> 'EventType': ...

    def set_summary_template(self, summary: unicode) -> 'EventType': ...

    def set_story_template(self, story: unicode) -> 'EventType': ...

    def set_version(self, version: int) -> 'EventType': ...

    def validate_template(self, template: unicode, ontology: edxml.ontology.Ontology) -> 'EventType': ...

    def validate(self) -> 'EventType': ...

    @classmethod
    def create_from_xml(cls, type_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'EventType': ...

    def update(self, event_type: 'EventType') -> 'EventType': ...

    def generate_xml(self) -> etree.Element: ...

    def get_singular_property_names(self) -> List[str]: ...

    def get_mandatory_property_names(self) -> List[str]: ...

    def validate_event_structure(self, event: edxml.EDXMLEvent) -> 'EventType': ...

    def validate_event_objects(self, event: edxml.EDXMLEvent) -> 'EventType': ...

    def generate_relax_ng(self, ontology: edxml.ontology.Ontology, namespaced: bool=False) -> etree.ElementTree: ...
