Reading EDXML Data Streams
==========================

The EDXML SDK features several classes and subpackages for parsing EDXML data streams, all based on the excellent `lxml library <http://lxml.de/>`_. All EDXML parsers are incremental, which allows for developing efficient system components that process a never ending stream of input events. All EDXML parsers are based on the EDXMLParserBase_ class, which has several subclasses for specific purposes. During parsing, the parser generates calls to a set of callback methods which can be overridden to process input data. There are callbacks for processing events and tracking ontology updates.

Besides extending a parser class and overriding callbacks, there is secondary mechanism specifically for processing events. EDXML parsers allow callbacks to be registered for specific event types or events from specific sources. These callbacks can be any Python callable. This allows EDXML data streams to be processed using a set of classes, each of which registered with the parser to process specific event data. The parser takes care of routing the events to the appropriate class.

The EDXMLParserBase_ class has two types of subclasses, *push parsers* and *pull parsers*. Pull parsers read from a provided file-like object in a blocking fashion. Push parsers need to be actively fed with string data. Push parsers provide control over the input process, which allows implementing efficient low latency event processing components.

The two most used EDXML parsers are EDXMLPullParser_ and EDXMLPushParser_. For the specific purpose of extracting ontology data from EDXML data, there are EDXMLOntologyPullParser_ and EDXMLOntologyPushParser_. The latter pair of classes skip event data and only invoke callbacks when ontology information is received.

- EDXMLParserBase_
- EDXMLParserBase_
- EDXMLPushParser_
- EDXMLPullParser_
- EDXMLOntologyPushParser_
- EDXMLOntologyPullParser_

edxml.EDXMLParserBase
---------------------
.. _EDXMLParserBase:

.. autoclass:: edxml.EDXMLParserBase
    :special-members: __init__
    :members:
    :member-order: groupwise
    :private-members: _parsedOntology, _parsedEvent
    :show-inheritance:

edxml.EDXMLPushParser
---------------------
.. _EDXMLPushParser:

.. autoclass:: edxml.EDXMLPushParser
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EDXMLPullParser
---------------------
.. _EDXMLPullParser:

.. autoclass:: edxml.EDXMLPullParser
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EDXMLOntologyPushParser
-----------------------------
.. _EDXMLOntologyPushParser:

.. autoclass:: edxml.EDXMLOntologyPushParser
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EDXMLOntologyPullParser
-----------------------------
.. _EDXMLOntologyPullParser:

.. autoclass:: edxml.EDXMLOntologyPullParser
    :special-members: __init__
    :members:
    :show-inheritance:

