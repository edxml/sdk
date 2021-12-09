Writing EDXML Data
==================

The EDXML SDK features several components for producing EDXML data, all based on the excellent `lxml library <http://lxml.de/>`_. Data generation is incremental, which allows for developing efficient system components that generate or process EDXML data in a streaming fashion.

EDXMLWriter
-----------

The EDXMLWriter_ class is the prime, low level EDXML generator. For most practical use cases a :doc:`transcoder <transcoding>` offers a superior means for generating EDXML data.

Using the EDXML writer is pretty straight forward, as the following example demonstrates:

.. literalinclude:: ../edxml/examples/event_writer.py
  :language: Python

Class Documentation
^^^^^^^^^^^^^^^^^^^
.. _`EDXMLWriter`:

.. autoclass:: edxml.EDXMLWriter
    :members:
    :show-inheritance:
