=================
Concept Graph API
=================

Concept graphs are collections of `Node`_ instances connected by edges. The edges represent inferences and are instances of the `Inference`_ class. Virtually all interaction with the graph takes place using the `ConceptInstanceGraph`_ class. While the nodes and edges are exposed when extracting mining results, they are not commonly accessed directly.

Mining is initiated using *seeds*. A seed is an initial graph node from which a concept instance is grown by iterative associative reasoning, taking the seed as starting point.

The graph can be mined in two different ways. Either the graph is mined from a specific seed selected by the API user. Alternatively, the API is requested to auto-select the most promising seed. Automatic seed selection and mining can be repeated to obtain a set of concept instances that 'covers' the entire graph, yielding a complete set of knowledge extracted from the event data.

Obtaining concept mining results is done by means of the :func:`extract_result_set <edxml.miner.graph.ConceptInstanceGraph.extract_result_set>` method of the `ConceptInstanceGraph`_ class. It returns a :class:`MinedConceptInstanceCollection` instance which is covered in detail :doc:`here <mining_result>`.

Class Documentation
-------------------

The class documentation can be found below.

ConceptInstanceGraph
^^^^^^^^^^^^^^^^^^^^
.. _ConceptInstanceGraph:

.. autoclass:: edxml.miner.graph.ConceptInstanceGraph
    :members:
    :show-inheritance:

Node
^^^^
.. _Node:

.. autoclass:: edxml.miner.Node
    :members:
    :show-inheritance:


EventObjectNode
^^^^^^^^^^^^^^^
.. _EventObjectNode:

.. autoclass:: edxml.miner.node.EventObjectNode
    :members:
    :show-inheritance:


Inference
^^^^^^^^^
.. _Inference:

.. autoclass:: edxml.miner.inference.Inference
    :members:
    :show-inheritance:
