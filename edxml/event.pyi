# -*- coding: utf-8 -*-

import edxml

from collections import MutableMapping
from lxml import etree
from typing import Dict, Union, Generator, List, Set, Iterable
from edxml.EDXMLBase import EvilCharacterFilter


class EDXMLEvent(MutableMapping):

    def __init__(self, properties: Dict[str, List[unicode]], event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, content: unicode = None) -> None:

        self._properties = ...    # type: Dict[str, Set[unicode]]
        self._event_type_name = ...  # type: str
        self._source_uri = ...     # type: str
        self._parents = ...       # type: Set[str]
        self._content = ...       # type: unicode
        self._foreign_attribs = ... # type: Dict[str, str]

    def __str__(self) -> unicode: ...

    def __delitem__(self, key: str) -> None: ...

    def __setitem__(self, key: str, value: Union[str, Iterable[unicode]]) -> None: ...

    def __len__(self) -> int: ...

    def __getitem__(self, key: str) -> Set[unicode]: ...

    def __contains__(self, key: str) -> bool: ...

    def __iter__(self) -> Generator[Dict[str, Set[unicode]], None, None]: ...

    def get_any(self, property_name: str, default: str=None) -> Union[unicode, None]: ...

    def copy(self) -> 'EDXMLEvent': ...

    @classmethod
    def create(cls, properties: Dict[str, Iterable[unicode]], event_type_name: str = None, source_uri: str = None,
               parents: List[str] = None, content: unicode = None) -> 'EDXMLEvent': ...

    def get_type_name(self) -> str: ...

    def get_source_uri(self) -> str: ...

    def get_properties(self) -> Dict[str, Set[unicode]]: ...

    def get_explicit_parents(self) -> List[str]: ...

    def get_content(self) -> unicode: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    @classmethod
    def create_from_xml(cls, event_type_name: str, source_uri: str, event_element: etree.Element) -> 'EDXMLEvent': ...

    def set_properties(self, properties: Dict[str, Iterable[unicode]]) -> 'EDXMLEvent': ...

    def copy_properties_from(self, source_event: 'EDXMLEvent', property_map: Dict[str, str]) -> 'EDXMLEvent': ...

    def move_properties_from(self, source_event: 'EDXMLEvent', property_map: Dict[str, str]) -> 'EDXMLEvent': ...

    def set_type(self, event_type_name: str) -> 'EDXMLEvent': ...

    def set_content(self, content: unicode) -> 'EDXMLEvent': ...

    def set_source(self, source_uri: str) -> 'EDXMLEvent': ...

    def add_parents(self, parent_hashes: List[str]) -> 'EDXMLEvent': ...

    def set_parents(self, parent_hashes: List[str]) -> 'EDXMLEvent': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'EDXMLEvent': ...

    def merge_with(self, colliding_events: List['EDXMLEvent'], ontology: edxml.ontology.Ontology) -> bool: ...

    def compute_sticky_hash(self, ontology: edxml.ontology.Ontology, encoding: str ='hex'): ...


class ParsedEvent(EDXMLEvent, EvilCharacterFilter, etree.ElementBase):

    def __init__(self, properties: Dict[str, Iterable[unicode]], event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, content: unicode = None) -> None:
        super(EDXMLEvent).__init__(properties, event_type_name, source_uri, parents, content)
        self.__properties = ...  # type: Dict[str, Set[unicode]]

    def flush(self) -> 'ParsedEvent': ...

    def copy(self) -> 'ParsedEvent': ...

    @classmethod
    def create_element(cls, properties: Dict[str, Iterable[unicode]], parents: List[str] = None,
                       content: unicode = None) -> etree.Element: ...

    def get_type_name(self) -> str: ...

    def get_explicit_parents(self) -> List[str]: ...

    def get_content(self) -> unicode: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    @classmethod
    def create_from_xml(cls, event_type_name: str, source_uri: str, event_element: etree.Element) -> 'ParsedEvent': ...

    def set_properties(self, properties: Dict[str, Iterable[unicode]]) -> 'ParsedEvent': ...

    def copy_properties_from(self, source_event: 'ParsedEvent', property_map: Dict[str, str]) -> 'ParsedEvent': ...

    def move_properties_from(self, source_event: 'ParsedEvent', property_map: Dict[str, str]) -> 'ParsedEvent': ...

    def set_type(self, event_type_name: str) -> 'ParsedEvent': ...

    def set_content(self, content: unicode) -> 'ParsedEvent': ...

    def set_source(self, source_uri: str) -> 'ParsedEvent': ...

    def add_parents(self, parent_hashes: List[str]) -> 'ParsedEvent': ...

    def set_parents(self, parent_hashes: List[str]) -> 'ParsedEvent': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'ParsedEvent': ...

    def merge_with(self, colliding_events: List['ParsedEvent'], ontology: edxml.ontology.Ontology) -> bool: ...

    def compute_sticky_hash(self, ontology: edxml.ontology.Ontology, encoding: str='hex'): ...


class EventElement(EDXMLEvent, EvilCharacterFilter):

    def __init__(self, properties: Dict[str, Iterable[unicode]], event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, content: unicode = None) -> None:
        super(EDXMLEvent).__init__(properties, event_type_name, source_uri, parents, content)
        self.__properties = ...  # type: Dict[str, Set[unicode]]
        self.__element = ...      # type: etree.Element

    def get_element(self) -> etree.Element: ...

    def copy(self) -> 'EventElement': ...

    @classmethod
    def create_element(cls, properties: Dict[str, List[unicode]], parents: List[str] = None,
                       content: unicode = None) -> etree.Element: ...

    def get_type_name(self) -> str: ...

    def get_explicit_parents(self) -> List[str]: ...

    def get_content(self) -> unicode: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    @classmethod
    def create_from_xml(cls, event_type_name: str, source_uri: str, event_element: etree.Element) -> 'EventElement': ...

    @classmethod
    def create_from_event(cls, event: EDXMLEvent) -> 'EventElement': ...

    def set_properties(self, properties: Dict[str, Iterable[unicode]]) -> 'EventElement': ...

    def copy_properties_from(self, source_event: 'EventElement', property_map: Dict[str, str]) -> 'EventElement': ...

    def move_properties_from(self, source_event: 'EventElement', property_map: Dict[str, str]) -> 'EventElement': ...

    def set_type(self, event_type_name: str) -> 'EventElement': ...

    def set_content(self, content: unicode) -> 'EventElement': ...

    def set_source(self, source_uri: str) -> 'EventElement': ...

    def add_parents(self, parent_hashes: List[str]) -> 'EventElement': ...

    def set_parents(self, parent_hashes: List[str]) -> 'EventElement': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'EventElement': ...

    def merge_with(self, colliding_events: List['EventElement'], ontology: edxml.ontology.Ontology) -> bool: ...

    def compute_sticky_hash(self, ontology: edxml.ontology.Ontology, encoding: str ='hex'): ...
