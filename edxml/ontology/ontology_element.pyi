# -*- coding: utf-8 -*-
from edxml.ontology import EventType
from lxml import etree

def ontology_element_upgrade_error(
        element_name: str, old: VersionedOntologyElement, new: VersionedOntologyElement,
) -> None: ...

def event_type_element_upgrade_error(
        element_name: str, old: OntologyElement, new: OntologyElement, old_type: EventType, new_type: EventType
) -> None: ...

class OntologyElement(object):
    """
    Class representing an EDXML ontology element
    """

    def validate(self) -> bool: ...

    def update(self, element: 'OntologyElement') -> 'OntologyElement': ...

    def __cmp__(self, other: 'OntologyElement') -> bool: ...

    def generate_xml(self) -> etree.Element: ...

class VersionedOntologyElement(OntologyElement):

    def get_version(self) -> int: ...
