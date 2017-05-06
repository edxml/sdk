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

Ontology bricks are EDXML ontology element definitions wrapped in a Python module. As such, they facilitate sharing ontology elements between multiple projects. This is especially useful for developing multiple EDXML data sources that generate mutually compatible ontologies.

Ontology bricks are limited to sharing object type definitions and concept definitions, because these are the only ontology elements for which it makes sense to share them. A simple import of an ontology brick is sufficient to make them available to the Ontology class. Definitions from an imported ontology brick will be automatically added to any Ontology instance that you create, on demand. For example, when an event type definition is added to an Ontology instance, any missing object types and concepts that the event type refers to will be looked up in the imported bricks. Any object types and concepts that are provided by the bricks will be automatically added to your Ontology instance.

Besides sharing ontology elements, defining bricks is an elegant way to define object types and concepts that you will use in your EDXML generator, weather these will be shared with other projects or not.

In order to make the automatic addition of brick elements work, the Python source file that defines the brick must contain a call to ``edxml.ontology.Ontology.RegisterBrick`` to register itself with the Ontology class. For example, if your brick class is named MyBrick, the source file must contain the command::

  edxml.ontology.Ontology.RegisterBrick(MyBrick)

.. autoclass:: edxml.ontology.Brick
    :special-members: __init__
    :members:
    :show-inheritance:
