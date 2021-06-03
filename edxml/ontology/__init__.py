# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

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
..  autoclass:: EventTypeFactory
    :members:
    :show-inheritance:
..  autoclass:: EventTypeParent
    :members:
    :show-inheritance:
..  autoclass:: EventTypeAttachment
    :members:
    :show-inheritance:
..  autoclass:: EventSource
    :members:
    :show-inheritance:
..  autoclass:: Ontology
    :members:
    :show-inheritance:
"""


from .ontology_element import OntologyElement, VersionedOntologyElement
from .util import normalize_xml_token
from .ontology import Ontology
from .data_type import DataType
from .object_type import ObjectType
from .event_type import EventType
from .event_property import EventProperty
from .event_property_concept import PropertyConcept
from .event_property_relation import PropertyRelation
from .event_source import EventSource
from .event_type_parent import EventTypeParent
from .event_type_attachment import EventTypeAttachment
from .concept import Concept
from .brick import Brick
from .event_type_factory import EventTypeFactory


__all__ = ['OntologyElement', 'DataType', 'EventType', 'EventProperty', 'PropertyRelation', 'EventSource',
           'EventTypeParent', 'ObjectType', 'Concept', 'Ontology', 'Brick', 'PropertyConcept', 'EventTypeAttachment',
           'normalize_xml_token', 'VersionedOntologyElement', 'EventTypeFactory']
