# -*- coding: utf-8 -*-
import hashlib

from edxml.ontology import EventType, Ontology

from collections import MutableMapping, OrderedDict, MutableSet
from lxml import etree
from typing import Dict, Union, Generator, List, Set, Iterable, Any, Optional


class PropertyObjectSet(set, MutableSet):
    def __init__(self, property_name, objects=None, update=None):
        super().__init__()
        ...

class PropertySet(OrderedDict):
    def __init__(self, properties=None, update_property=None):
        super().__init__()

    def _update_property(self, property_name: str, values): ...

    def replace_object_set(self, property_name, object_set) -> None: ...


class AttachmentSet(OrderedDict):
    def __init__(self, attachments: Dict[str, Dict[str, str]] = None, update_attachment=None):
        super().__init__()

    def _update_attachment(self, attachment_name: str, value: Optional[str]): ...


class EDXMLEvent(MutableMapping):

    def __init__(self, properties: Optional[Dict[str, Union[Any, Set[Any]]]] = None,
                 event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, attachments: Dict[str, Dict[str, str]] = None,
                 foreign_attribs: Dict[str, str]=None) -> None:

        self._properties = ...    # type: PropertySet
        self._event_type_name = ...  # type: str
        self._source_uri = ...     # type: str
        self._parents = ...       # type: Set[str]
        self._attachments = ...     # type: AttachmentSet
        self._foreign_attribs = ... # type: Dict[str, str]
        self._replace_invalid_characters = ... #type: bool

    def __update_property(self, key: str, value: Any):   ...

    def __update_attachment(self, attachment_name: str, attachment_id: str, value: str) -> None: ...

    def __str__(self) -> str: ...

    def __delitem__(self, key: str) -> None: ...

    def __setitem__(self, key: str, value: Union[Any, Set[Any]]) -> None: ...

    def __len__(self) -> int: ...

    def __getitem__(self, key: str) -> Set[Any]: ...

    def __contains__(self, key: str) -> bool: ...

    def __iter__(self) -> Generator[Dict[str, Set[str]], None, None]: ...

    @property
    def properties(self) -> Union[PropertySet, Dict[Any, Set[Any]]]: ...

    @properties.setter
    def properties(self, new_properties: Dict[str, Union[Any, Iterable[Any]]]) -> None: ...

    @property
    def attachments(self) -> Union[AttachmentSet, Dict[str, Dict[str, str]]]: ...

    @attachments.setter
    def attachments(self, new_attachments: Dict[str, Dict[str, str]]) -> None: ...

    def replace_invalid_characters(self, replace: bool=True) -> 'EDXMLEvent': ...

    def get_any(self, property_name: str, default=None) -> Union[Any, None]: ...

    def copy(self) -> 'EDXMLEvent': ...

    @classmethod
    def create(cls, properties: Dict[str, Union[Any, Set[Any]]] = None,
               event_type_name: str = None, source_uri: str = None,
               parents: List[str] = None, attachments: Dict[str, Dict[str, str]] = None) -> 'EDXMLEvent': ...

    def get_type_name(self) -> str: ...

    def get_source_uri(self) -> str: ...

    def get_properties(self) -> Union[PropertySet, Dict[str, Set[Any]]]: ...

    def get_parent_hashes(self) -> List[str]: ...

    def get_attachments(self) -> Union[AttachmentSet, Dict[str, Dict[str, str]]]: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    def get_element(self, sort: bool = False) -> etree.Element: ...

    def set_properties(self, properties: Dict[str, Union[Any, Set[Any]]]) -> 'EDXMLEvent': ...

    def copy_properties_from(self, source_event: 'EDXMLEvent', property_map: Dict[str, str]) -> 'EDXMLEvent': ...

    def move_properties_from(self, source_event: 'EDXMLEvent', property_map: Dict[str, str]) -> 'EDXMLEvent': ...

    def set_type(self, event_type_name: str) -> 'EDXMLEvent': ...

    def set_attachment(self, name: str, attachment: Union[Optional[str], List[Optional[str]], Dict[str, Optional[str]]]) -> 'EDXMLEvent': ...

    def set_source(self, source_uri: str) -> 'EDXMLEvent': ...

    def add_parents(self, parent_hashes: List[str]) -> 'EDXMLEvent': ...

    def set_parents(self, parent_hashes: List[str]) -> 'EDXMLEvent': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'EDXMLEvent': ...

    def compute_sticky_hash(self, event_type: EventType, hash_function: callable = hashlib.sha1, encoding: str ='hex')\
            -> str: ...

    def is_valid(self, ontology: Ontology) -> bool: ...

class ParsedEvent(EDXMLEvent, etree.ElementBase):

    def __init__(self, properties: Dict[str, Union[Any, Set[Any]]] = None,
                 event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, attachments: Dict[str, Dict[str, str]] = None,
                 foreign_attribs: Dict[str, str]=None) -> None:
        super().__init__(properties, event_type_name, source_uri, parents, attachments)
        self.__properties = ...  # type: Dict[str, Set[str]]

    def replace_invalid_characters(self, replace: bool=True) -> etree.Element: ...

    def flush(self) -> 'ParsedEvent': ...

    def copy(self) -> 'ParsedEvent': ...

    def _sort(self): ...

    def get_type_name(self) -> str: ...

    def get_parent_hashes(self) -> List[str]: ...

    def get_attachments(self) -> Dict[str, Dict[str, str]]: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    def set_properties(self, properties: Dict[str, Union[Any, Set[Any]]]) -> 'ParsedEvent': ...

    def copy_properties_from(self, source_event: EDXMLEvent, property_map: Dict[str, str]) -> 'ParsedEvent': ...

    def move_properties_from(self, source_event: EDXMLEvent, property_map: Dict[str, str]) -> 'ParsedEvent': ...

    def set_type(self, event_type_name: str) -> 'ParsedEvent': ...

    def set_attachment(self, name: str, attachment: Union[Optional[str], List[Optional[str]], Dict[str, Optional[str]]]) -> 'ParsedEvent': ...

    def set_source(self, source_uri: str) -> 'ParsedEvent': ...

    def add_parents(self, parent_hashes: List[str]) -> 'ParsedEvent': ...

    def set_parents(self, parent_hashes: List[str]) -> 'ParsedEvent': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'ParsedEvent': ...


class EventElement(EDXMLEvent):

    def __init__(self, properties: Dict[str, Union[Any, Set[Any]]] = None,
                 event_type_name: str = None, source_uri: str = None,
                 parents: List[str] = None, attachments: Dict[str, Dict[str]] = None,
                 foreign_attribs: Dict[str, str]=None) -> None:
        super().__init__(properties, event_type_name, source_uri, parents, attachments)
        self.__properties = ...  # type: Dict[str, Set[str]]
        self.__element = ...      # type: etree.Element


    def replace_invalid_characters(self, replace: bool=True) -> 'EventElement': ...

    def copy(self) -> 'EventElement': ...

    def _sort(self): ...

    def get_type_name(self) -> str: ...

    def get_parent_hashes(self) -> List[str]: ...

    def get_attachments(self) -> Dict[str, Dict[str, str]]: ...

    def get_foreign_attributes(self) -> Dict[str, str]: ...

    @classmethod
    def create_from_event(cls, event: EDXMLEvent) -> 'EventElement': ...

    def set_properties(self, properties: Dict[str, Union[Any, Set[Any]]]) -> 'EventElement': ...

    def copy_properties_from(self, source_event: EDXMLEvent, property_map: Dict[str, str]) -> 'EventElement': ...

    def move_properties_from(self, source_event: EDXMLEvent, property_map: Dict[str, str]) -> 'EventElement': ...

    def set_type(self, event_type_name: str) -> 'EventElement': ...

    def set_attachment(self, name: str, attachment: Union[Optional[str], List[Optional[str]], Dict[str, Optional[str]]]) -> 'EventElement': ...

    def set_source(self, source_uri: str) -> 'EventElement': ...

    def add_parents(self, parent_hashes: List[str]) -> 'EventElement': ...

    def set_parents(self, parent_hashes: List[str]) -> 'EventElement': ...

    def set_foreign_attributes(self, attribs: Dict[str,str]) -> 'EventElement': ...
