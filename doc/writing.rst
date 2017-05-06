Generating EDXML Data Streams
=============================

The EDXML SDK features several classes and subpackages for producing EDXML data streams, all based on the excellent `lxml library <http://lxml.de/>`_. Data generation is incremental, which allows for developing efficient system components that generate a never ending stream of events. The EDXMLWriter_ class is the prime, low level EDXML generator. The SimpleEDXMLWriter_ class is a variant with a friendlier interface. This is the recommended class to use for EDXML writing, if you are willing to trade a bit of performance for ease of use.

For the specific task of generating EDXML data from JSON, the `JSON transcoder module`_ can be used. It provides convenient features for mapping JSON records to EDXML event types and for using multiple separate transcoders to process input containing a mix of several types of JSON records.

- EDXMLWriter_
- SimpleEDXMLWriter_
- `JSON transcoder module`_

edxml.SimpleEDXMLWriter
-----------------------
.. _SimpleEDXMLWriter:

.. autoclass:: edxml.SimpleEDXMLWriter
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EDXMLWriter
-----------------
.. _EDXMLWriter:

.. autoclass:: edxml.EDXMLWriter
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.transcode module
----------------------

.. automodule:: edxml.transcode
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.transcode.json module
---------------------------
.. _`JSON transcoder module`:

.. automodule:: edxml.transcode.json
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.transcode.xml module
--------------------------
.. _`XML transcoder module`:

.. automodule:: edxml.transcode.xml
    :special-members: __init__
    :members:
    :show-inheritance:
