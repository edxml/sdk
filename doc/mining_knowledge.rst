==================
The Knowledge Base
==================

A :ref:`knowledge base <KnowledgeBase>` stores two types of information originating from EDXML data:

- Concept instances
- Universals

As detailed in the `EDXML specification <http://edxml.org/spec/>`_, universals are things like names and descriptions for object values, originating from specific property relations.

A knowledge base can be populated using a :class:`Miner <edxml.miner.Miner>`. By feeding EDXML events and ontologies to a Miner it will incrementally extract universals and store them inside its knowledge base. Feeding EDXML data will also grow the internal :doc:`reasoning graph <mining_graph>` of the Miner. When all EDXML data is loaded, the reasoning graph is complete and concept mining can be triggered using the :func:`mine() <edxml.miner.Miner.mine()>` method.

Rather than feeding :class:`EDXMLEvent <edxml.EDXMLEvent>` and :class:`Ontology <edxml.ontology.Ontology>` objects to a Miner it is also possible to parse EDXML data directly into a Miner. That can be done using either a :ref:`KnowledgePullParser <KnowledgePullParser>` or a :ref:`KnowledgePushParser <KnowledgePushParser>`.

A quick example to illustrate:

.. literalinclude:: ../edxml/examples/mining_knowledge_base.py
  :language: Python

Concept Mining Seeds
--------------------

Concept mining always needs a starting seed. A starting seed is a specific event object that is used as a starting point for traversing the reasoning graph. The mining process will then 'grow' the concept by iteratively adding adjacent event objects in the graph to the concept. Just calling the :func:`mine() <edxml.miner.knowledge.KnowledgeParserBase.mine()>` method without any arguments will automatically find suitable seeds and mine them until all event objects in the graph have been assigned to a concept instance. In stead of automatic seed selection, a seed can be passed to the :func:`mine() <edxml.miner.knowledge.KnowledgeParserBase.mine()>` method. That will cause only this one seed to be mined and a single concept being added to the knowledge base.

Class Documentation
-------------------

The class documentation can be found below.

- Miner_
- KnowledgeBase_
- KnowledgePullParser_
- KnowledgePushParser_
- KnowledgeParserBase_

Miner
^^^^^
.. _Miner:

..  autoclass:: edxml.miner.Miner
    :members:
    :show-inheritance:

KnowledgeBase
^^^^^^^^^^^^^
.. _KnowledgeBase:

..  autoclass:: edxml.miner.knowledge.KnowledgeBase
    :members:
    :show-inheritance:

KnowledgePullParser
^^^^^^^^^^^^^^^^^^^
.. _KnowledgePullParser:

..  autoclass:: edxml.miner.parser.KnowledgePullParser
    :members:
    :show-inheritance:

KnowledgePushParser
^^^^^^^^^^^^^^^^^^^
.. _KnowledgePushParser:

..  autoclass:: edxml.miner.parser.KnowledgePushParser
    :members:
    :show-inheritance:

KnowledgeParserBase
^^^^^^^^^^^^^^^^^^^
.. _KnowledgeParserBase:

..  autoclass:: edxml.miner.parser.KnowledgeParserBase
    :members:
    :show-inheritance:
