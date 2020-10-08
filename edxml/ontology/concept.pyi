# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any, Generator, Optional
from typing import Dict

from edxml.ontology import OntologyElement


class Concept(OntologyElement):
    NAME_PATTERN = ...
    FUZZY_MATCHING_PATTERN = ...

    def __init__(self, ontology: edxml.ontology.Ontology, name: str, display_name_singular: str = None,
                 display_name_plural: str = None, description: str = None) -> None:
        self._attr = ...    # type: Dict[str, Any]
        self._ontology = ...  # type: edxml.ontology.Ontology
        self.__versions = ... # type: Dict[int, 'Concept']

    def _child_modified_callback(self) -> 'Concept': ...

    def _set_attr(self, key: str, value): ...

    @classmethod
    def concept_names_share_branch(cls, a: str, b:str) -> bool: ...

    @classmethod
    def concept_name_is_specialization(cls, concept_name: str, specialization_concept_name: str) -> bool: ...

    def get_name(self) -> str: ...

    def get_display_name_singular(self) -> str: ...

    def get_display_name_plural(self) -> str: ...

    def get_description(self) -> str: ...

    def get_version(self) -> int: ...

    def set_description(self, description: str) -> 'Concept': ...

    def set_display_name(self, singular: str, plural: str = None) -> 'Concept': ...

    def set_version(self, version: int) -> 'Concept': ...

    def upgrade(self) -> 'Concept': ...

    def validate(self) -> 'Concept': ...

    @classmethod
    def create_from_xml(cls, type_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'Concept': ...

    def update(self, concept: 'Concept') -> 'Concept': ...

    def generate_xml(self) -> etree.Element: ...

    @classmethod
    def generate_specializations(cls, concept_name: str, parent_concept_name: Optional[str]= '') -> Generator[str]: ...
