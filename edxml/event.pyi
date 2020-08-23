# -*- coding: utf-8 -*-

import edxml

from collections import MutableMapping, OrderedDict
from lxml import etree
from typing import Dict, Union, Generator, List, Set, Iterable, Tuple, Any


class PropertySet(OrderedDict):
    def __init__(self, properties=None, update_property=None):
        self.__properties = Dict[PropertyObjectSet]

    def _update_property(self, property_name: str, values): ...

    def replace_object_set(self, property_name, object_set) -> None: ...

    def items(self) -> List[Tuple]: ...

    def keys(self) -> List: ...

    def values(self) -> List: ...

    def get(self, property_name: str, default=None): ...

    def copy(self) -> 'PropertySet': ...

    def __len__(self) -> int: ...

    def __setitem__(self, key, value): ...

    def __getitem__(self, item): ...

    def __delitem__(self, key): ...

class EDXMLEvent(MutableMapping):

    def __init__(self, properties: Dict[str, Set[str]], event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, attachments: Dict[str, str] = {}) -> None:

        self.properties = ...     # type: Dict[str, Set[str]]
        self._properties = ...    # type: Dict[str, Set[str]]
        self._event_type_name = ...  # type: str
        self._source_uri = ...     # type: str
        self._parents = ...       # type: Set[str]
        self._attachments = ...     # type: Dict[str, str]
        self._foreign_attribs = ... # type: Dict[str, str]
        self._replace_invalid_characters = ... #type: bool

    def __str__(self) -> str: ...

    def __delitem__(self, key: str) -> None: ...

    def __setitem__(self, key: str, value: Union[str, Iterable[str]]) -> None: ...

    def __len__(self) -> int: ...

    def __getitem__(self, key: str) -> Set[str]: ...

    def __contains__(self, key: str) -> bool: ...

    def __iter__(self) -> Generator[Dict[str, Set[str]], None, None]: ...

    def replace_invalid_characters(self, replace: bool=True) -> 'EDXMLEvent': ...

    def get_any(self, property_name: str, default: str=None) -> Union[str, None]: ...

    def copy(self) -> 'EDXMLEvent': ...

    @classmethod
    def create(cls, properties: Dict[str, Iterable[str]], event_type_name: str = None, source_uri: str = None,
               parents: List[str] = None, attachments: Dict[str, str] = {}) -> 'EDXMLEvent': ...

    def sort(self) -> 'EDXMLEvent': ...

    def get_type_name(self) -> str: ...

    def get_source_uri(self) -> str: ...

    def get_properties(self) -> Dict[str, Set[str]]: ...

    def get_explicit_parents(self) -> List[str]: ...

    def get_attachments(self) -> Dict[str, str]: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    def get_element(self) -> etree.Element: ...

    @classmethod
    def create_from_xml(cls, event_element: etree.Element) -> 'EDXMLEvent': ...

    def set_properties(self, properties: Dict[str, Iterable[str]]) -> 'EDXMLEvent': ...

    def copy_properties_from(self, source_event: 'EDXMLEvent', property_map: Dict[str, str]) -> 'EDXMLEvent': ...

    def move_properties_from(self, source_event: 'EDXMLEvent', property_map: Dict[str, str]) -> 'EDXMLEvent': ...

    def set_type(self, event_type_name: str) -> 'EDXMLEvent': ...

    def set_attachments(self, attachments: Dict[str, str]) -> 'EDXMLEvent': ...

    def set_source(self, source_uri: str) -> 'EDXMLEvent': ...

    def add_parents(self, parent_hashes: List[str]) -> 'EDXMLEvent': ...

    def set_parents(self, parent_hashes: List[str]) -> 'EDXMLEvent': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'EDXMLEvent': ...

    def compute_sticky_hash(self, ontology: edxml.ontology.Ontology, encoding: str ='hex'): ...


class ParsedEvent(EDXMLEvent, etree.ElementBase):

    def __init__(self, properties: Dict[str, Iterable[str]], event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, attachments: Dict[str, str] = {}) -> None:
        super(EDXMLEvent).__init__(properties, event_type_name, source_uri, parents, attachments)
        self.__properties = ...  # type: Dict[str, Set[str]]

    def replace_invalid_characters(self, replace: bool=True) -> etree.Element: ...

    def flush(self) -> 'ParsedEvent': ...

    def copy(self) -> 'ParsedEvent': ...

    @classmethod
    def create_element(cls, properties: Dict[str, Iterable[str]], parents: List[str] = None,
                       attachments: Dict[str, str] = {}) -> etree.Element: ...

    def get_type_name(self) -> str: ...

    def get_explicit_parents(self) -> List[str]: ...

    def get_attachments(self) -> Dict[str, str]: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    @classmethod
    def create_from_xml(cls, event_element: etree.Element) -> 'ParsedEvent': ...

    def set_properties(self, properties: Dict[str, Iterable[str]]) -> 'ParsedEvent': ...

    def copy_properties_from(self, source_event: 'ParsedEvent', property_map: Dict[str, str]) -> 'ParsedEvent': ...

    def move_properties_from(self, source_event: 'ParsedEvent', property_map: Dict[str, str]) -> 'ParsedEvent': ...

    def set_type(self, event_type_name: str) -> 'ParsedEvent': ...

    def set_attachments(self, attachments: Dict[str, str]) -> 'ParsedEvent': ...

    def set_source(self, source_uri: str) -> 'ParsedEvent': ...

    def add_parents(self, parent_hashes: List[str]) -> 'ParsedEvent': ...

    def set_parents(self, parent_hashes: List[str]) -> 'ParsedEvent': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'ParsedEvent': ...

    def merge_with(self, colliding_events: List['ParsedEvent'], ontology: edxml.ontology.Ontology) -> bool: ...

    def compute_sticky_hash(self, ontology: edxml.ontology.Ontology, encoding: str='hex'): ...


class EventElement(EDXMLEvent):

    def __init__(self, properties: Dict[str, Iterable[str]], event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, attachments: Dict[str, str] = {}) -> None:
        super(EDXMLEvent).__init__(properties, event_type_name, source_uri, parents, attachments)
        self.__properties = ...  # type: Dict[str, Set[str]]
        self.__element = ...      # type: etree.Element

    def replace_invalid_characters(self, replace: bool=True) -> 'EventElement': ...

    def copy(self) -> 'EventElement': ...

    @classmethod
    def create_element(cls, properties: Dict[str, List[str]], parents: List[str] = None,
                       attachments: Dict[str, str] = {}) -> etree.Element: ...

    def get_type_name(self) -> str: ...

    def get_explicit_parents(self) -> List[str]: ...

    def get_attachments(self) -> Dict[str, str]: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    @classmethod
    def create_from_xml(cls, event_element: etree.Element) -> 'EventElement': ...

    @classmethod
    def create_from_event(cls, event: EDXMLEvent) -> 'EventElement': ...

    def set_properties(self, properties: Dict[str, Iterable[str]]) -> 'EventElement': ...

    def copy_properties_from(self, source_event: 'EventElement', property_map: Dict[str, str]) -> 'EventElement': ...

    def move_properties_from(self, source_event: 'EventElement', property_map: Dict[str, str]) -> 'EventElement': ...

    def set_type(self, event_type_name: str) -> 'EventElement': ...

    def set_attachments(self, attachments: Dict[str, str]) -> 'EventElement': ...

    def set_source(self, source_uri: str) -> 'EventElement': ...

    def add_parents(self, parent_hashes: List[str]) -> 'EventElement': ...

    def set_parents(self, parent_hashes: List[str]) -> 'EventElement': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'EventElement': ...

    def merge_with(self, colliding_events: List['EventElement'], ontology: edxml.ontology.Ontology) -> bool: ...

    def compute_sticky_hash(self, ontology: edxml.ontology.Ontology, encoding: str ='hex'): ...
