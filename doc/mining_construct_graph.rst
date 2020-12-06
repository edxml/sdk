==================
Graph Construction
==================

A graph can be constructed using the `GraphConstructor`_ and `EventCollector`_ classes. An EventCollector is an :ref:`EDXMLPullParser <EDXMLPullParser>`. Using it to parse some EDXML data will populate the graph.

A quick example to illustrate:

.. literalinclude:: ../tests/examples/event_collector.py
  :language: Python

edxml.miner.GraphConstructor
----------------------------
.. _GraphConstructor:

.. autoclass:: edxml.miner.GraphConstructor
    :members:
    :show-inheritance:

edxml.miner.EventCollector
--------------------------
.. _EventCollector:

.. autoclass:: edxml.miner.EventCollector
    :members:
    :show-inheritance:
