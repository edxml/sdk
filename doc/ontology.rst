EDXML Ontology
==============

When reading an EDXML data stream, the parser consumes both events and ontology information and provides an interface to access both. On the other hand, EDXML writers require providing an ontology matching the events that are written. In the EDXML SDK, ontology information is represented by instances of the Ontology_ class. This class is supported by several peripheral classes representing `event types`_, `event properties`_, `object types`_, `data types`_ and `event sources`_.

- Ontology_
- EventType_
- EventProperty_
- ObjectType_
- DataType_
- EventSource_
- Brick_

edxml.ontology.Ontology
-----------------------
.. py:module:: edxml.ontology
.. _Ontology:

.. autoclass:: edxml.ontology.Ontology
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ontology.EventType
------------------------
.. _`event types`:
.. _EventType:

.. autoclass:: edxml.ontology.EventType
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ontology.EventTypeParent
------------------------------
.. _`event type parents`:
.. _EventTypeParent:

.. autoclass:: edxml.ontology.EventTypeParent
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ontology.EventProperty
----------------------------
.. _`event properties`:
.. _EventProperty:

.. autoclass:: edxml.ontology.EventProperty
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ontology.ObjectType
-------------------------
.. _`object types`:
.. _ObjectType:

.. autoclass:: edxml.ontology.ObjectType
    :members:
    :show-inheritance:

edxml.ontology.DataType
-----------------------
.. _`data types`:
.. _DataType:

.. autoclass:: edxml.ontology.DataType
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ontology.EventSource
--------------------------
.. _`event sources`:
.. _EventSource:

.. autoclass:: edxml.ontology.EventSource
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ontology.Brick
--------------------
.. _`ontology bricks`:
.. _Brick:

.. autoclass:: edxml.ontology.Brick
    :special-members: __init__
    :members:
    :show-inheritance:
