Composite Data Sources
======================

Some data sources may produce multiple types of data records. We will call these data sources *composite sources*. Other sources may produce data records that are too complex to represent using a single EDXML event type. We will refer to these sources as *complex sources*. Writing a transcoder for these types of data sources requires producing various types of output events. Below, we will cover some techniques of handling these sources.

Complex Sources
---------------

If you are struggling to write an event story describing an output record of some data source, you are most likely dealing with a complex source. Event stories should be fairly simple. If your event story ends up reading like a section of a book rather than a paragraph, you should probably split your event type into multiple sub-types.

When analysing data records that have been split up into multiple EDXML events, it is generally desirable to be able to collect all EDXML events that represent a single complex input record. This can be achieved by having the event types refer to one another. The simplest way to do that is by having multiple EDXML events share an object that is unique to the input record. A more elegant method is to create parent-child relationships between events. For some input records, parent-child relationships may be a natural fit. For example, many XML data sources produce data structures that incorporate some kind of a hierarchy.

TODO: Use VirusTotal as example case, show code snippets

Composite Sources
-----------------

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
----------------------------

The EDXML SDK features the :class:`edxml.transcode.Transcoder` class, which can be used to write transcoders for composite data sources. The class has two extensions :class:`edxml.transcode.object.ObjectTranscoder` and :class:`edxml.transcode.xml.XmlTranscoder` for transcoding XML and JSON based data sources. Adding support for other types of data sources is fairly straight forward. By extending the ``ObjectTranscoder`` or ``XmlTranscoder`` classes, a collection of transcoders can be written for each of the various types of input data records.

Next to the ``Transcoder`` class, the SDK features the :class:`edxml.transcode.TranscoderMediator` class. This class is the mediator between the input data and the collection of transcoders. Like the transcoder class, the mediator class has two extensions :class:`edxml.transcode.xml.XmlTranscoderMediator` and :class:`edxml.transcode.object.ObjectTranscoderMediator` for processing XML data and sets of arbitrary Python objects. A mediator allows a transcoder to be registered for each input record type. The mediator will then automatically parse the input data, determine the record type for each input record and invoke the correct transcoder to produce EDXML events. The mediator determines which transcoder to use by means of *selectors*. What a selector looks like depends on the type of transcoder. For instance, a selector in the XML transcoder is an XPath expression. When a transcoder registers itself with the mediator, it specifies a selector that will select the input data records that the transcoder is designed to transcode.

The ``Transcoder`` class can automatically create EDXML events for you if you provide it with some information about how to map fields from the input records to event properties. For example, the ``XmlTranscoder`` class has an ``PROPERTY_MAP`` constant that can be populated with XPath expressions that point into the XML data, along with associated event properties. The ``ObjectTranscoder`` class has an ``PROPERTY_MAP`` constant that works in a similar fashion. It supports a dotted syntax to allow reaching anywhere into the input JSON record to gather event properties, like this:

.. code-block:: python

  {'fieldname.0.subfieldname': 'property-name'}

The resulting EDXML events are passed to the post_process() method of the transcoder where they can be post-processed if necessary.

Transcoding Data Flow
---------------------

Let us have a look at how input data flows through the various components to finally produce EDXML output. In general, reading the input data records is the responsibility of you, the transcoder developer. You need to process the input data to the point where it can be chopped up in individual input records. Each input record can then be passed to the :func:`edxml.transcode.TranscoderMediator.process()` method of the mediator. From that moment on, the EDXML SDK takes over processing from you. Depending on the mediator implementation that you use, you may get lucky and also leave the parsing of input data to the mediator. For example, the :class:`edxml.transcode.xml.XmlTranscoderMediator` features a :func:`edxml.transcode.xml.XmlTranscoderMediator.parse()` method that accepts file names and file-like objects. The XML mediator will use the XPath selectors from all registered transcoders to extract XML elements from the input data and pass them to the ``Process()`` method of the mediator.

The process() method of the mediator will inspect the input record and check which of the registered selectors matches the record. The mediator will then pass the input record to the :func:`edxml.transcode.Transcoder.generate()` method of the transcoder. This method is a Python generator that will use the various class constants to generate one or more EDXML events from the input record. The generated EDXML events are intercepted inside the ``Process()`` method of the mediator. The mediator will then pass each EDXML event to the :func:`edxml.transcode.Transcoder.PostProcess()` method of the transcoder, which is also a generator. The default implementation of this generator just passes the generated EDXML events unmodified. Transcoder developers can override it to edit the generated EDXML events before they are output.

Finally, the EDXML events produced by the ``post_process()`` method are written to the output EDXML stream.

To recapitulate, during the transcoding process the data flows through various class methods like this:

1. :func:`edxml.transcode.TranscoderMediator.process()`
2. :func:`edxml.transcode.Transcoder.generate()`
3. :func:`edxml.transcode.Transcoder.post_process()`

Now that the data flow is clear, we can also see how to control the transcoding process by overriding class methods. First of all, the ``process()`` method if the mediator inspects the passed input record and decides which transcoder to invoke. Overriding this method allows the decision making process to be manipulated. We will have a look at a specific use case later. Second, the ``generate()`` method of the transcoder performs the actual transcoding: It generates EDXML events from the input record that is passed into it. Overriding it allows transcoder developers to edit the input records before the parent implementation uses them to create EDXML events. And lastly, the ``PostProcess()`` method of the transcoder performs optional post-processing on the EDXML events.

Most use cases involve overriding either or both of the methods of the Transcoder class. The decision on which methods to override depends on the type of processing that you want to do, personal preference and performance requirements. For example, removing irrelevant fields from the input records early in the transcoding process may yield a performance gain. If you wish to generate multiple output events from a single input record, overriding the ``post_process()`` method may be the most convenient way to do that. It could be done by distributing the properties of a single generated EDXML super-event into multiple output events or by performing analysis on the generated event and yielding the analysis results in the form of multiple EDXML events. If you are transcoding XML data, manipulating the XML elements by overriding the ``generate()`` method may yield performance gains.

Generating Ontology Elements
----------------------------

Each transcoder is responsible for generating the event types, object types and concepts for the events that it generates. Generating these can be done by overriding three methods from the Transcoder class. Of these three methods, the method that is responsible for generating the event type is a bit special because the parent class provides an implementation for it that generates event types from class constants. Using this implementation in stead of implementing your own allows a transcoder to specify event type name, properties, event story templates, etc by setting class constants in stead of writing code. This may yield a simpler transcoder implementation, so be sure to check that out. Please refer to the documentation of the :class:`edxml.transcode.Transcoder` class for full details.

The class methods for generating object types and concepts need not be overridden if you use ontology bricks. Should you prefer to define an object type or concept using the generator methods, your override will look something like this example:

.. code-block:: python

  def generate_concepts(self):
    yield self._ontology.create_concept('file')\
                        .set_description('a computer resource for recording data')\
                        .set_display_name('file')



Handling Many Event Types
-------------------------

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

the event story template for the fallback event type might look like this:

.. epigraph::

  *On [[FULLDATETIME:time]], an event of type '[[type]]' occurred. The event contains the following data fields:{ user1 = [[user1]].}{ user2 = [[user2]].}{ user3 = [[user3]].}{ user4 = [[user4]].}{ user5 = [[user5]].}*

Pretty lame, just like the original data. Every data source gets what it deserves, right? Using a fallback event type allows you to select the most valuable types of input data record, develop a dedicated EDXML event type for them and use the fallback event type for the remaining input records.

.. epigraph::

  *If you store the original input record inside each output event (as event content), you can re-process previously transcoded data whenever you add a transcoder for a specific type of input event. This way, you can gradually extend the collection of transcoders over time.*

The ``Mediator`` class fully supports the concept of a fallback event type. Attaching a fallback transcoder to the mediator requires two steps:

1. Register your fallback transcoder with the mediator using ``RECORD_OF_UNKNOWN_TYPE`` as selector. The mediator will then invoke the fallback transcoder whenever it encounters an input record for which no transcoder is registered.
2. The ``TYPE_MAP`` dictionary constant in the fallback transcoder must contain just one key: :keyword:`None`. The value is the name of the generic fallback event type produced by the fallback transcoder, as usual.

In case you are writing an XML transcoder, the question may arise how the mediator knows how to extract XML elements for the fallback transcoder given the fact that it will not use an XPath expression to register itself. The answer lies in the `tags` argument of the :func:`edxml.transcode.xml.XmlTranscoderMediator.parse()` method. This arguments allows specifying a list of XML element names of elements that will be considered for feeding to a transcoder. Any considered element that does not match any of the registered XPath expressions will be given to the fallback transcoder, if any.

.. epigraph::

  *Note that this issue does not arise with the JSON transcoder because you, the transcoder developer, are responsible for providing the JSON input records.*

Depending on the structure of your input data, relying on the name of the XML element may be more or less ideal. An alternative approach is to register your fallback transcoder using an XPath expression that selects *all* XML elements that you want the mediator to consider for feeding to a transcoder. In this scenario, an XML element may match the XPath of multiple transcoders. In that case, the mediator will select the transcoder that was registered using the *shortest* XPath expression. For example, in case you have a transcoder for a specific type of input record at XPath

  ``/records/record/[@type='whatever']``

and a fallback transcoder for records at XPath

  ``/records/record``

the mediator will use the fallback transcoder for all records except for records of type 'whatever', which will be routed to the transcoder for that specific record type.

Multi-Field Selectors
---------------------

Sometimes, you may need to inspect multiple fields in the input records in order to decide which transcoder to use. In general, mediators only allow specifying a single record field as a selector. This problem may be solved by overriding the ``process()`` method of the mediator. As pointed out earlier, this method is where input records begin their journey to become EDXML output events. We can override it, modify the input record and then invoke the original method implementation. Suppose that our input records are JSON records containing two integer fields ``type`` and ``subtype``. We want to route input records to transcoders depending on the value of both fields. This can be achieved by dynamically replacing these fields with a single field that combines the two, like this:

 .. code-block:: python

  from edxml.transcode.object import ObjectTranscoderMediator

  class MyMediator(ObjectTranscoderMediator):

    TYPE_FIELD = 'ctype'

    def process(self, json):
      json['ctype'] = str(json['type']) + ':' + str(json['subtype'])
      super().process(json)

Now we can register a transcoder using a record type of ``42:4673`` for instance. If you need even more complex record routing logic, writing a full replacement for the ``process()`` method is the way to go.

Parsing broken XML input
------------------------

In an ideal world, the input data for your transcoder is produced by a data source that was written by developers who knew exactly what they were doing. In practise though, you *will* come across data that is horribly broken. When dealing with JSON data, the EDXML SDK expects *you* to provide valid input data records. This means that you are free to do whatever you need to validate, filter, edit and fix the JSON data before handing it over to the mediator. For XML input data, things are slightly different. Parsing is done by the mediator itself, which reads the input data from a file. By default, it *will* break when you feed it broken XML data. There are two approaches that you can take to transcode broken XML data:

1. Ask the XML parser to try and ignore errors
2. Dynamically fix the input data using a file-like object

Ignoring errors is the simplest solution and can be done by using the ``recover=True`` argument of the :func:`edxml.transcode.xml.XmlTranscoderMediator.parse()` method. This will make the parser try to recover from errors. However, error recovery may result in data loss and other side effects. If you happen to know in what way the input data is broken, writing a file-like object that fixes the input data just before parsing may yield a more satisfactory result. The idea is that you write a Python class that acts like a file and pass an instance to the ``Parse()`` method of the XML transcoder. The transcoder will then read data from this class instance, not from the original input data. The class instance accepts read requests from the XML transcoder. It responds by reading from the original input data, fixing it and returning the resulting fixed XML data. Using a custom file-like object like this allows you to get in between the original data file and the parser reading from it.

Debugging Transcoders
---------------------

Since real life input data can be horrendously inconsistent or downright broken, debugging your transcoder is part of the effort. There are a couple of things that may get in your way while developing transcoders that you should be aware of. For instance, the EDXML writer buffers output events by default. This may lead to confusion when the EDXML output that precedes an exception is incomplete. Also, by default the mediator will catch any exceptions thrown during processing, print a warning and continue. These warnings are easily missed.

By calling :func:`edxml.transcode.TranscoderMediator.debug()`, debug mode is enabled. In debug mode, output buffering is disabled and the transcoding process will abort whenever something goes wrong. Also, the transcoding process produces more informative warning messages.

Running Transcoders in Production
---------------------------------

When running a transcoder in production, there is a trade-off to make between high availability and correctness / completeness of the output. In case a bug slips through in the development process, the transcoder might fail on rare corner cases. A transcoder can be made to respond to these failures in two ways. Either it swallows the exception, skips the offending input record and continues operating normally. Or it crashes, requiring the problem to be resolved before continuing.  The mediator offers some features to configure its behavior and customize its response to problems.

Generating an EDXML event that is invalid raises an exception. By default, the mediator does not handle this exception, or any other exceptions that might be raised by a transcoder. YOU CAN HANDLE THESE, OR ALLOW CRASH, OR USE IGNORE INVALID EVENTS, BELOW.

The :func:`edxml.transcode.TranscoderMediator.ignore_invalid_events()` method will enable skipping any EDXML output events that are not valid. Events that failed to produce due to exceptions raised during the transcoding of an input record are also considered invalid events. The invalid events will be ignored and processing will continue normally.
