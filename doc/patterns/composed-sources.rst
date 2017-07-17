Composed Data Sources
=====================

Some data sources may produce multiple types of data records. We will call these data sources *composite sources*. Other sources may produce data records that are too complex to represent using a single EDXML event type. We will refer to these sources as *complex sources*. Writing a transcoder for these types of data sources requires producing various types of output events. Below, we will cover some techniques of handling these sources.

Complex Sources
===============

If you are struggling to write an event story describing an output record of some data source, you are most likely dealing with a complex source. Event stories should be fairly simple. If your event story ends up reading like a section of a book rather than a paragraph, you should probably split your event type into multiple sub-types.

When analysing data records that have been split up into multiple EDXML events, it is generally desirable to be able to collect all EDXML events that represent a single complex input record. This can be achieved by having the event types refer to one another. The simplest way to do that is by having multiple EDXML events share an object that is unique to the input record. A more elegant method is to create parent-child relationships between events. For some input records, parent-child relationships may be a natural fit. For example, many XML data sources produce data structures that incorporate some kind of a hierarchy.

TODO: Use VirusTotal as example case, show code snippets

Composite Sources
=================

Composite sources produce data records that have different meanings. This may be very explicit, for example when the input records have truly different structure and a different set of fields. The composite character may also be more implicit. Some sources *appear* to produce a single type of data record but on close examination, the records each represent quite different things. An example of an implicitly composite data source may be a source producing JSON records that look like this:

.. code-block:: javascript

   {
     "time":        2016-10-11T21:04:36.167,
     "source":      "192.168.1.20",
     "destination": "192.168.10.43",
     "type":        6473,
     "user1":       "alice",
     "user2":       32,
     "user3":       "",
     "user4":       "",
     "user5":       "",
   }

The above JSON record is from a data source that produces records that all have the same set of fields, but only four out of nine fields has the same meaning for all records. The meaning of the five 'user' fields varies depending on the value of the ``type`` field. This is a pattern commonly found in data sources that allow the user to extend its data model, while employing a simple rigid SQL database schema at the same time. Data from sources like these is an analyst's worst nightmare and - rest assured - also not the EDXML data modeler's favourite. So much for the bad news. The good news is that an EDXML transcoder can convert these data records into EDXML events that are far easier to work with, and the EDXML SDK provides some nice tools to make that happen.

Transcoders in the EDXML SDK
============================

The EDXML SDK features a class called ``Transcoder`` in the ``edxml.Transcode`` module, which can be used to write transcoders for composite data sources. The class has two extensions ``JsonTranscoder`` and ``XmlTranscoder`` for transcoding XML and JSON based data sources. Adding support for other types of data sources is fairly straight forward. By extending the ``JsonTranscoder`` or ``XmlTranscoder`` classes, a collection of transcoders can be written for each of the various types of input data records.

Next to the ``Transcoder`` class, the SDK features a `TranscoderMediator` class. This class is the mediator between the input data and the collection of transcoders. The mediator enables you to specify how to differentiate between the various types of input data records by means of a *selector*. What a selector looks like depends on the type of transcoder. For instance, a selector in the XML transcoder is an XPath expression. The mediator allows a transcoder to be registered for each input record type. The mediator will then automatically parse the input data, determine the record type for each input record and invoke the correct transcoder to produce EDXML events.

The ``Transcoder`` class can even create the EDXML events for you if you provide it with some information about how to map fields from the input records to event properties. For example, the ``XmlTranscoder`` class has an ``XPATH_MAP`` constant that can be populated with XPath expressions that point into the XML data, along with associated event properties. The ``JsonTranscoder`` class has an ``ATTRIBUTE_MAP`` constant that works in a similar fashion. It supports a dotted syntax to allow reaching anywhere into the input JSON record to gather event properties, like this:

.. code-block:: python

  {'fieldname.0.subfieldname': 'property-name'}

The resulting EDXML events are passed to the PostProcess() method of the transcoder where they can be post-processed if necessary.

Generating Ontology Elements
============================

Each transcoder is responsible for generating the event types, object types and concepts for the events that it generates. Generating these can be done by overriding three methods from the Transcoder class. Of these three methods, the method that is responsible for generating the event type is a bit special because the parent class provides an implementation for it that generates event types from class constants. Using this implementation in stead of implementing your own allows a transcoder to specify event type name, properties, reporter strings, etc by setting class constants in stead of writing code. This may yield a simpler transcoder implementation, so be sure to check that out. Please refer to the Python class documentation for full details.

The class methods for generating object types and concepts need not be overridden if you use ontology bricks. Should you prefer to define an object type or concept using the generator methods, your override will look something like this example:

.. code-block:: python

  def GenerateConcepts(self):
    yield self._ontology.CreateConcept('file')\
                        .SetDescription('a computer resource for recording data')\
                        .SetDisplayName('file')



Handling Many Event Types
=========================

Some data sources may produce too many types of events to fully model in EDXML. There are two ways to tackle this problem. The first option is the use of a *fallback event type*. A fallback event type is a highly generic EDXML event type that deliberately does not tell the full story. It closely resembles the structure of the original data records and does not attempt to enrich the input data with semantics. This allows a single EDXML event type to cover all types of input data records that lack a dedicated transcoder. The output EDXML will still be complete, but only a subset of the input record types is modeled properly. For example, when the input data records look like this:

.. code-block:: javascript

   {
     "time":        2016-10-11T21:04:36.167,
     "source":      "192.168.1.20",
     "destination": "192.168.10.43",
     "type":        6473,
     "user1":       "alice",
     "user2":       32,
     "user3":       "",
     "user4":       "",
     "user5":       "",
   }

the reporter string for the fallback event type might look like this:

.. epigraph::

  *On [[FULLDATETIME:time]], an event of type '[[type]]' occurred. The event contains the following data fields:{ user1 = [[user1]].}{ user2 = [[user2]].}{ user3 = [[user3]].}{ user4 = [[user4]].}{ user5 = [[user5]].}*

Pretty lame, just like the original data. Every data source gets what it deserves, right? Using a fallback event type allows you to select the most valuable types of input data record, develop a dedicated EDXML event type for them and use the fallback event type for the remaining input records.

.. epigraph::

  *If you store the original input record inside each output event (as event content), you can re-process previously transcoded data whenever you add a transcoder for a specific type of input event. This way, you can gradually extend the collection of transcoders over time.*

The ``Mediator`` class fully supports the concept of a fallback event type. You can register your fallback transcoder with the mediator using ``RECORD_OF_UNKNOWN_TYPE`` as selector. The mediator will then invoke the fallback transcoder whenever it encounters an input records for which no transcoder is registered.
