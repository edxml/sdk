EDXML Ontology Bricks
=====================

EDXML ontology bricks are commonly used to share object types and concepts. The EDXML Foundation keeps an `online repository <https://github.com/edxml/bricks/>`_ of shared definitions.

Bricks can be registered with an :class:`Ontology <edxml.ontology.Ontology>`_ instance. After registering a brick, you can create an event type and refer to the object types and concepts from the brick. The ontology will automatically fetch the referred ontology elements from the registered brick and include them in the ontology. The following example illustrates this:

.. literalinclude:: ../edxml/examples/brick_register.py
  :language: Python


edxml.ontology.Brick
--------------------
.. _`ontology bricks`:
.. _Brick:

.. autoclass:: edxml.ontology.Brick
    :members:
    :show-inheritance:
