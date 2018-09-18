# -*- coding: utf-8 -*-
from lxml import etree

class OntologyElement(object):
    """
    Class representing an EDXML ontology element
    """

    def validate(self) -> bool: ...

    def update(self, element: 'OntologyElement') -> 'OntologyElement': ...

    def __cmp__(self, other: 'OntologyElement') -> bool: ...

    def generate_xml(self) -> etree.Element: ...
