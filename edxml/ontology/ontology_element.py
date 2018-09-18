# -*- coding: utf-8 -*-


class OntologyElement(object):
    """
    Class representing an EDXML ontology element
    """

    def validate(self):
        return self

    def update(self, object_type):
        return self

    def __cmp__(self, other):
        return 0

    def generate_xml(self):
        return None
