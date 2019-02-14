"""
This sub-package contains classes that represent EDXML
ontology elements, like event types, object types, event
sources, and so on.

..  autoclass:: OntologyElement
    :members:
    :show-inheritance:
..  autoclass:: ObjectType
    :members:
    :show-inheritance:
..  autoclass:: DataType
    :members:
    :show-inheritance:
..  autoclass:: Concept
    :members:
    :show-inheritance:
..  autoclass:: EventProperty
    :members:
    :show-inheritance:
..  autoclass:: PropertyRelation
    :members:
    :show-inheritance:
..  autoclass:: PropertyConcept
    :members:
    :show-inheritance:
..  autoclass:: EventType
    :members:
    :show-inheritance:
..  autoclass:: EventTypeParent
    :members:
    :show-inheritance:
..  autoclass:: EventSource
    :members:
    :show-inheritance:
..  autoclass:: Ontology
    :members:
    :show-inheritance:
"""
from __future__ import absolute_import
from edxml.ontology.ontology_element import OntologyElement
from edxml.ontology.data_type import DataType
from edxml.ontology.event_type import EventType
from edxml.ontology.event_property import EventProperty
from edxml.ontology.event_property_concept import PropertyConcept
from edxml.ontology.event_property_relation import PropertyRelation
from edxml.ontology.event_source import EventSource
from edxml.ontology.event_type_parent import EventTypeParent
from edxml.ontology.object_type import ObjectType
from edxml.ontology.concept import Concept
from edxml.ontology.ontology import Ontology
from edxml.ontology.brick import Brick


__all__ = ['OntologyElement', 'DataType', 'EventType', 'EventProperty', 'PropertyRelation', 'EventSource',
           'EventTypeParent', 'ObjectType', 'Concept', 'Ontology', 'Brick', 'PropertyConcept']
