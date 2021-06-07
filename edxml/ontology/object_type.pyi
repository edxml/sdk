# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any, Optional
from typing import Dict

from edxml.ontology import OntologyElement


class ObjectType(OntologyElement):
    NAME_PATTERN = ...
    FUZZY_MATCHING_PATTERN = ...

    def __init__(self, ontology: edxml.ontology.Ontology, name: str, display_name_singular: str = None,
                 display_name_plural: str = None, description: str = None,
                 data_type: str = 'string:0:mc:u', unit_name: str = None, unit_symbol: str = None,
                 prefix_radix: int = None, compress: bool = False, xref: str = None, fuzzy_matching: str = 'none',
                 regex_hard: str = None, regex_soft=None) -> None:

        self.__versions = ... # type: Dict[int, 'ObjectType']
        self.__attr = ...  # type: Dict[str, Any]
        self.__ontology = ...  # type: edxml.ontology.Ontology

    def _child_modified_callback(self) -> 'ObjectType': ...

    def _set_attr(self, key: str, value): ...

    def get_name(self) -> str: ...

    def get_display_name_singular(self) -> str: ...

    def get_display_name_plural(self) -> str: ...

    def get_description(self) -> str: ...

    def get_data_type(self) -> edxml.ontology.DataType: ...

    def get_unit_name(self) -> str: ...

    def get_unit_symbol(self) -> str: ...

    def get_prefix_radix(self) -> int: ...

    def is_compressible(self) -> bool: ...

    def get_xref(self) -> Optional[str]: ...

    def get_fuzzy_matching(self) -> Optional[str]: ...

    def get_regex_hard(self) -> Optional[str]: ...

    def get_regex_soft(self) -> Optional[str]: ...

    def get_version(self) -> int: ...

    def set_description(self, description: str) -> 'ObjectType': ...

    def set_data_type(self, data_type: edxml.ontology.DataType) -> 'ObjectType': ...

    def set_xref(self, url: str) -> 'ObjectType': ...

    def set_prefix_radix(self, radix: int) -> 'ObjectType': ...

    def set_display_name(self, singular: str, plural: str = None) -> 'ObjectType': ...

    def set_unit(self, unit_name: str, unit_symbol: str) -> 'ObjectType': ...

    def set_regex_hard(self, pattern: str) -> 'ObjectType': ...

    def set_regex_soft(self, pattern: str) -> 'ObjectType': ...

    def set_fuzzy_matching_attribute(self, attribute: str) -> 'ObjectType': ...

    def set_version(self, version: int) -> 'ObjectType': ...

    def upgrade(self) -> 'ObjectType': ...

    def fuzzy_match_head(self, length: int) -> 'ObjectType': ...

    def fuzzy_match_tail(self, length: int) -> 'ObjectType': ...

    def fuzzy_match_substring(self, pattern: str) -> 'ObjectType': ...

    def fuzzy_match_phonetic(self) -> 'ObjectType': ...

    def compress(self, is_compressible: bool =True) -> 'ObjectType': ...

    def generate_relaxng(self) -> etree.Element: ...

    def validate_object_value(self, value: str) -> 'ObjectType': ...

    def validate(self) -> 'ObjectType': ...

    @classmethod
    def create_from_xml(cls, type_element: etree.Element, ontology: edxml.ontology.Ontology) -> 'ObjectType': ...

    def update(self, object_type: 'ObjectType') -> 'ObjectType': ...

    def generate_xml(self) -> etree.Element: ...
