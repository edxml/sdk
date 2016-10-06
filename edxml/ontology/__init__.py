"""
This sub-package contains classes that represent EDXML
ontology elements, like event types, object types, event
sources, and so on.

..  autoclass:: ObjectType
    :members:
    :show-inheritance:
..  autoclass:: DataType
    :members:
    :show-inheritance:
..  autoclass:: EventProperty
    :members:
    :show-inheritance:
..  autoclass:: PropertyRelation
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
"""
from data_type import DataType
from event_property import EventProperty
from event_property_relation import PropertyRelation
from event_source import EventSource
from event_type import EventType
from event_type_parent import EventTypeParent
from object_type import ObjectType
