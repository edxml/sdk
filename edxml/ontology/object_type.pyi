# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any
from typing import Dict

from edxml.ontology import OntologyElement


class ObjectType(OntologyElement):
    NAME_PATTERN = ...
    FUZZY_MATCHING_PATTERN = ...

    def __init__(self, ontology: edxml.ontology.Ontology, name: str, display_name_singular: str = None,
                 display_name_plural: str = None, description: str = None,
                 data_type: str = 'string:0:cs:u', compress: bool = False, fuzzy_matching: str = 'none',
                 regexp: str = '[\s\S]*') -> None:

        self.__attr = ...  # type: Dict[str, Any]
        self.__ontology = ...  # type: edxml.ontology.Ontology

    def _child_modified_callback(self) -> 'ObjectType': ...

    def _set_attr(self, key: str, value): ...

    def get_name(self) -> str: ...

    def get_display_name_singular(self) -> str: ...

    def get_display_name_plural(self) -> str: ...

    def get_description(self) -> str: ...

    def get_data_type(self) -> edxml.ontology.DataType: ...

    def is_compressible(self) -> bool: ...

    def get_fuzzy_matching(self) -> str: ...

    def get_regexp(self) -> str: ...

    def get_version(self) -> int: ...

    def set_description(self, description: str) -> 'ObjectType': ...

    def set_data_type(self, data_type: edxml.ontology.DataType) -> 'ObjectType': ...

    def set_display_name(self, singular: str, plural: str = None) -> 'ObjectType': ...

    def set_regexp(self, pattern: str) -> 'ObjectType': ...

    def set_fuzzy_matching_attribute(self, attribute: str) -> 'ObjectType': ...

    def set_version(self, version: int) -> 'ObjectType': ...

    def fuzzy_match_head(self, length: int) -> 'ObjectType': ...

    def fuzzy_match_tail(self, length: int) -> 'ObjectType': ...

    def fuzzy_match_substring(self, pattern: str) -> 'ObjectType': ...

    def fuzzy_match_phonetic(self) -> 'ObjectType': ...

    def compress(self, is_compressible: bool =True) -> 'ObjectType': ...

    def generate_relaxng(self) -> etree.Element: ...

    def validate_object_value(self, value: unicode) -> 'ObjectType': ...

    def validate(self) -> 'ObjectType': ...

    @classmethod
    def create_from_xml(cls, type_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'ObjectType': ...

    def update(self, object_type: 'ObjectType') -> 'ObjectType': ...

    def generate_xml(self) -> etree.Element: ...
