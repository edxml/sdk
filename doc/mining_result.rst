======================
Concept Mining Results
======================

Concept mining results are represented by the `ConceptInstanceCollection`_ class. These are basically just collections of `ConceptInstance`_. Concept instances expose lists of `ConceptAttribute`_.

The concept attributes contain an object value, an EDXML object type name and one or more EDXML concept names that it is associated with. The names of the concept attributes consist of the name of an object type, a colon and optionally an extension, as per `the EDXML specification <http://edxml.org/spec>`_ .

The :func:`from_json() <edxml.miner.result.from_json>` function can be used to re-create a concept instance collection from a previously generated JSON string.

edxml.miner.result.ConceptInstanceCollection
-------------------------------------------------
.. _ConceptInstanceCollection:

.. autoclass:: edxml.miner.result.ConceptInstanceCollection
    :members:
    :show-inheritance:

edxml.miner.result.ConceptInstance
-------------------------------------------------
.. _ConceptInstance:

.. autoclass:: edxml.miner.result.ConceptInstance
    :members:
    :show-inheritance:

edxml.miner.result.ConceptAttribute
-------------------------------------------------
.. _ConceptAttribute:

.. autoclass:: edxml.miner.result.ConceptAttribute
    :members:
    :show-inheritance:

.. autofunction:: edxml.miner.result.from_json

The following two classes are extensions exposing graph details like nodes and inferences.

edxml.miner.result.MinedConceptInstanceCollection
-------------------------------------------------
.. _MinedConceptInstanceCollection:

.. autoclass:: edxml.miner.result.MinedConceptInstanceCollection
    :members:
    :show-inheritance:

edxml.miner.result.MinedConceptInstance
-------------------------------------------------
.. _MinedConceptInstance:

.. autoclass:: edxml.miner.result.MinedConceptInstance
    :members:
    :show-inheritance:
