EDXML Ontologies
================

When reading an EDXML data stream, the parser consumes both events and ontology information and provides an interface to access both. On the other hand, EDXML writers require providing an ontology matching the events that are written. In the EDXML SDK, ontology information is represented by instances of the Ontology_ class. This class is supported by several peripheral classes representing `event types`_, `event properties`_, `object types`_, `data types`_ and `event sources`_.

Ontologies can be populated by using the various named constructors of the Ontology_ class. Alternatively, ontology elements can be fetched from an :doc:`Ontology Brick <bricks>`. or generated using an :doc:`event type factory <event_type_factory>`.

Ontology Description & Visualization
------------------------------------

EDXML data sources can provide a wealth of knowledge. Learning if and how that knowledge will help you in your data analysis tasks requires studying its output ontology and how it fits into other domain ontologies that you might use. Unless an EDXML data source can just tell you.

The :func:`describe_producer_rst() <edxml.ontology.description.describe_producer_rst>` function can do just that. Given an ontology it will list the object types and concepts that it uses and how it aids reasoning about data. For example, the description might say: *Identifies computers as network routers* or *Relates IP addresses to host names*. The name of the function indicates that the generated descriptions are meant for describing EDXML data producers such as data sources or data processors.

When designing an EDXML ontology, getting the relations and concept associations right is critical. A picture can be most helpful to review your design. Using the :func:`generate_graph_property_concepts() <edxml.ontology.visualization.generate_graph_property_concepts>` function you can generate a visualization showing the reasoning paths provided by a given ontology. It displays the concepts and object types and how they are connected.

API Documentation
-----------------

The API documentation can be found below.

*Ontology Elements*

- Ontology_
- EventType_
- EventTypeAttachment_
- EventProperty_
- PropertyConcept_
- ObjectType_
- Concept_
- DataType_
- EventSource_

*Base Classes*

- OntologyElement_
- VersionedOntologyElement_

*Functions*

- generate_graph_property_concepts_
- describe_producer_rst_

Ontology
^^^^^^^^
.. _Ontology:

.. autoclass:: edxml.ontology.Ontology
    :members:
    :show-inheritance:

EventType
^^^^^^^^^
.. _`event types`:
.. _EventType:

.. autoclass:: edxml.ontology.EventType
    :members:
    :show-inheritance:

EventTypeAttachment
^^^^^^^^^^^^^^^^^^^

.. _EventTypeAttachment:

.. autoclass:: edxml.ontology.EventTypeAttachment
    :members:
    :show-inheritance:

EventTypeParent
^^^^^^^^^^^^^^^
.. _`event type parents`:
.. _EventTypeParent:

.. autoclass:: edxml.ontology.EventTypeParent
    :members:
    :show-inheritance:

EventProperty
^^^^^^^^^^^^^
.. _`event properties`:
.. _EventProperty:

.. autoclass:: edxml.ontology.EventProperty
    :members:
    :show-inheritance:

PropertyConcept
^^^^^^^^^^^^^
.. _`property concept associations`:
.. _PropertyConcept:

.. autoclass:: edxml.ontology.PropertyConcept
    :members:
    :show-inheritance:

ObjectType
^^^^^^^^^^
.. _`object types`:
.. _ObjectType:

.. autoclass:: edxml.ontology.ObjectType
    :members:
    :show-inheritance:

Concept
^^^^^^^
.. _`concepts`:
.. _Concept:

.. autoclass:: edxml.ontology.Concept
    :members:
    :show-inheritance:

DataType
^^^^^^^^
.. _`data types`:
.. _DataType:

.. autoclass:: edxml.ontology.DataType
    :members:
    :show-inheritance:

EventSource
^^^^^^^^^^^
.. _`event sources`:
.. _EventSource:

.. autoclass:: edxml.ontology.EventSource
    :members:
    :show-inheritance:

OntologyElement
^^^^^^^^^^^^^^^
.. _OntologyElement:

.. autoclass:: edxml.ontology.OntologyElement
    :members:
    :show-inheritance:

VersionedOntologyElement
^^^^^^^^^^^^^^^^^^^^^^^^
.. _VersionedOntologyElement:

.. autoclass:: edxml.ontology.VersionedOntologyElement
    :members:
    :show-inheritance:

describe_producer_rst()
^^^^^^^^^^^^^^^^^^^^^^^
.. _describe_producer_rst:

.. automodule:: edxml.ontology.description
    :members:

generate_graph_property_concepts()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. _generate_graph_property_concepts:

.. automodule:: edxml.ontology.visualization
    :members:
