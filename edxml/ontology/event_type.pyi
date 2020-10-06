# -*- coding: utf-8 -*-
import edxml

from typing import List, Dict, Iterable, Tuple, Optional

from edxml import EDXMLEvent
from lxml import etree

from edxml.ontology import OntologyElement, PropertyRelation


class EventType(OntologyElement):

    NAME_PATTERN = ...
    CLASS_LIST_PATTERN = ...

    def __init__(self, ontology: edxml.ontology.Ontology, name: str, display_name_singular: str = None,
                 display_name_plural: str = None, description: str = None,
                 class_list: str = '', summary: str = 'no description available',
                 story: str = 'no description available', parent: edxml.ontology.EventTypeParent = None) -> None:

        self.__attr = ...              # type: Dict
        self.__properties = ...        # type: Dict[str, edxml.ontology.EventProperty]
        self.__relations = ...         # type: Dict[str, edxml.ontology.PropertyRelation]
        self.__parent = ...            # type: edxml.ontology.EventTypeParent
        self.__parent_description = ...  # type: str
        self.__attachments = {}         # type: Dict[str, edxml.ontology.EventTypeAttachment]
        self.__relax_ng = None          # type: etree.RelaxNG
        self.__ontology = ...           # type: edxml.ontology.Ontology

        self.__cached_unique_properties = ...  # type: Dict[str, edxml.ontology.EventProperty]
        self.__cached_hash_properties = ...    # type: Dict[str, edxml.ontology.EventProperty]

    def __getitem__(self, property_name: str) -> edxml.ontology.EventProperty: ...

    def _child_modified_callback(self) -> 'EventType': ...

    def _set_attr(self, key: str, value): ...

    @property
    def relations(self) -> Iterable[PropertyRelation]: ...

    def get_name(self) -> str: ...

    def get_description(self) -> str: ...

    def get_display_name_singular(self) -> str: ...

    def get_display_name_plural(self) -> str: ...

    def get_timespan_property_name_start(self) -> Optional[str]: ...

    def get_timespan_property_name_end(self) -> Optional[str]: ...

    def get_version_property_name(self) -> Optional[str]: ...

    def get_sequence_property_name(self) -> Optional[str]: ...

    def get_classes(self) -> List[str]: ...

    def get_properties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def get_unique_properties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def get_hash_properties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def get_property_relations(self, rtype: str=None, source:str=None, target:str=None) -> \
            Dict[str, edxml.ontology.PropertyRelation]: ...

    def get_attachment(self, name: str) -> edxml.ontology.EventTypeAttachment: ...

    def get_attachments(self) -> Dict[str, edxml.ontology.EventTypeAttachment]: ...

    def get_version(self) -> int: ...

    def has_class(self, class_name) -> bool: ...

    def is_unique(self) -> bool: ...

    def get_timespan_property_names(self) -> Tuple[Optional[str], Optional[str]]: ...

    def is_timeless(self) -> bool: ...

    def is_timeful(self) -> bool: ...

    def get_summary_template(self) -> str: ...

    def get_story_template(self) -> str: ...

    def get_parent(self) -> edxml.ontology.EventTypeParent: ...

    def create_property(self, name: str, object_type_name: str, description: str = None) -> edxml.ontology.EventProperty: ...

    def add_property(self, prop: edxml.ontology.EventProperty) -> 'EventType': ...

    def remove_property(self, property_name: str) -> 'EventType': ...

    def _select_relation_concepts(
            self, relation_type: str, source: str, target: str, source_concept_name: str, target_concept_name: str
    ) -> Tuple[edxml.ontology.Concept, edxml.ontology.Concept]: ...

    def create_relation(
            self, source: str, target: str, description: str, type: str, predicate: str,
            source_concept_name=None, target_concept_name=None, confidence: float = 1.0, directed: bool = True
    ) -> edxml.ontology.PropertyRelation: ...

    def add_relation(self, relation: edxml.ontology.PropertyRelation) -> 'EventType': ...

    def create_attachment(self, name: str) -> edxml.ontology.EventTypeAttachment: ...

    def add_attachment(self, attachment: edxml.ontology.EventTypeAttachment) -> 'EventType': ...

    def make_child(self, siblings_description: str, parent: 'EventType') -> edxml.ontology.EventTypeParent: ...

    def make_parent(self, parent_description, child: 'EventType') -> 'EventType': ...

    def set_description(self, description: str) -> 'EventType': ...

    def set_parent(self, parent: edxml.ontology.EventTypeParent) -> 'EventType': ...

    def add_class(self, class_name: str) -> 'EventType': ...

    def set_classes(self, class_names: Iterable[str]) -> 'EventType': ...

    def set_name(self, event_type_name: str) -> 'EventType': ...

    def set_display_name(self, singular: str, plural: str = None) -> 'EventType': ...

    def set_summary_template(self, summary: str) -> 'EventType': ...

    def set_story_template(self, story: str) -> 'EventType': ...

    def set_version(self, version: int) -> 'EventType': ...

    def set_timespan_property_name_start(self, property_name: str) -> 'EventType': ...

    def set_timespan_property_name_end(self, property_name: str) -> 'EventType': ...

    def set_version_property_name(self, property_name: str) -> 'EventType': ...

    def set_sequence_property_name(self, property_name: str) -> 'EventType': ...

    def evaluate_template(
            self, edxml_event: EDXMLEvent, which: str = 'story', capitalize: bool = True, colorize: bool = False
    ) -> str: ...

    def _validate_event_versioning(self) -> None: ...

    def _validate_event_sequencing(self) -> None: ...

    def validate(self) -> 'EventType': ...

    @classmethod
    def create_from_xml(cls, type_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'EventType': ...

    def _check_sub_element_upgrade(
            self, old: 'EventType', new: 'EventType', equal: bool, is_valid_upgrade: bool
    ) -> Tuple[bool, bool]: ...

    def _update_sub_elements(self, event_type: 'EventType') -> None: ...

    def update(self, event_type: 'EventType') -> 'EventType': ...

    def generate_xml(self) -> etree.Element: ...

    def get_singular_property_names(self) -> List[str]: ...

    def get_mandatory_property_names(self) -> List[str]: ...

    def validate_event_structure(self, event: edxml.EDXMLEvent) -> 'EventType': ...

    def validate_event_objects(self, event: edxml.EDXMLEvent, property_name: str=None) -> 'EventType': ...

    def validate_event_attachments(self, event: edxml.EDXMLEvent) -> 'EventType': ...

    def normalize_event_objects(self, event: edxml.EDXMLEvent, property_names: List[str]) -> 'EventType': ...

    def generate_relax_ng(self, ontology: edxml.ontology.Ontology, namespaced: bool=False) -> etree.ElementTree: ...

    def merge_events(self, events: List[edxml.EDXMLEvent]) -> edxml.EDXMLEvent: ...

    def _check_merge_conflict(self, events: List[edxml.EDXMLEvent], version_property: str) -> None: ...
