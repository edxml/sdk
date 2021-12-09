Reading EDXML Data
==================

The EDXML SDK features several classes and subpackages for parsing EDXML data streams, all based on the excellent `lxml library <http://lxml.de/>`_. All EDXML parsers are incremental, which allows for developing efficient system components that process a never ending stream of input events.

EDXML Parsers
-------------

All EDXML parsers are based on the EDXMLParserBase_ class, which has several subclasses for specific purposes. During parsing, the parser generates calls to a set of callback methods which can be overridden to process input data. There are callbacks for processing events and tracking ontology updates.

The EDXMLParserBase_ class has two types of subclasses, *push parsers* and *pull parsers*. Pull parsers read from a provided file-like object in a blocking fashion. Push parsers need to be actively fed with string data. Push parsers provide control over the input process, which allows implementing efficient low latency event processing components.

The two most used EDXML parsers are EDXMLPullParser_ and EDXMLPushParser_. For the specific purpose of extracting ontology data from EDXML data, there are EDXMLOntologyPullParser_ and EDXMLOntologyPushParser_. The latter pair of classes skip event data and only invoke callbacks when ontology information is received.

An example of using the pull parser is shown below:

.. literalinclude:: ../edxml/examples/parser_pull.py
  :language: Python

Besides extending a parser class and overriding callbacks, there is secondary mechanism specifically for processing events. EDXML parsers allow callbacks to be registered for specific event types or events from specific sources. These callbacks can be any Python callable. This allows EDXML data streams to be processed using a set of classes, each of which registered with the parser to process specific event data. The parser takes care of routing the events to the appropriate class.

EventCollection
---------------

In stead of reading EDXML data in a streaming fashion it can also be useful to read and access an EDXML document as a whole. This can be done using the EventCollection_ class. The following example illustrates this:

.. literalinclude:: ../edxml/examples/event_collection.py
  :language: Python

Class Documentation
-------------------

The class documentation of the various parsers can be found below.

- EDXMLParserBase_
- EDXMLPushParser_
- EDXMLPullParser_
- EDXMLOntologyPushParser_
- EDXMLOntologyPullParser_

EDXMLParserBase
^^^^^^^^^^^^^^^
.. _EDXMLParserBase:

.. autoclass:: edxml.EDXMLParserBase
    :members:
    :member-order: groupwise
    :show-inheritance:

EDXMLPushParser
^^^^^^^^^^^^^^^
.. _EDXMLPushParser:

.. autoclass:: edxml.EDXMLPushParser
    :members:
    :show-inheritance:

EDXMLPullParser
^^^^^^^^^^^^^^^
.. _EDXMLPullParser:

.. autoclass:: edxml.EDXMLPullParser
    :members:
    :show-inheritance:

EDXMLOntologyPushParser
^^^^^^^^^^^^^^^^^^^^^^^
.. _EDXMLOntologyPushParser:

.. autoclass:: edxml.EDXMLOntologyPushParser
    :members:
    :show-inheritance:

EDXMLOntologyPullParser
^^^^^^^^^^^^^^^^^^^^^^^
.. _EDXMLOntologyPullParser:

.. autoclass:: edxml.EDXMLOntologyPullParser
    :members:
    :show-inheritance:

EventCollection
^^^^^^^^^^^^^^^
.. _EventCollection:

.. autoclass:: edxml.EventCollection
    :members:
    :show-inheritance:
