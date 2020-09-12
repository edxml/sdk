# -*- coding: utf-8 -*-
from functools import total_ordering


@total_ordering
class OntologyElement(object):
    """
    Class representing an EDXML ontology element
    """

    def validate(self):
        return self

    def update(self, element):
        return self

    def __cmp__(self, other):
        return 0

    def __eq__(self, other):
        return 0

    def __ne__(self, other):
        return 0

    def __lt__(self, other):
        return 0

    def generate_xml(self):
        return None


class VersionedOntologyElement(OntologyElement):
    """
    An ontology element that is versioned, such as an object type,
    concept, event type or an event source.
    """

    def get_version(self):
        """

        Returns the version of the ontology element

        Returns:
            int: Element version
        """
        return 0
