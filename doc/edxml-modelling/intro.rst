Introduction to EDXML Data Modelling
====================================

EDXML is about transforming data into stories. Stories that both humans and machines can understand and reason about. This enables machines to read data much in the same way as a human being reads a novel, to learn while reading. Learning what the story is about and learning more and more as one paragraph is followed by another.

Modelling data in EDXML is the process of realizing what story the data tells and casting that into a model. EDXML has no predefined model. It provides the means to define whatever model fits your data best. This introduction will show what the process of data modelling looks like.

Understand Your Data
--------------------
EDXML data is represented by means of *events*. Each event represents a little story, like a paragraph in a novel. An event can represent many different things, like a database record, a document, an e-mail message or a financial transaction. What a particular event represents is determined by its event type.

One of the first questions to be answered when modelling data as EDXML is: How can the original data be broken down into events? To answer that question, the analogy of events as paragraphs in a novel is very helpful. A single paragraph never tells a full story. It contributes to a story by conveying some bits of information in a structured way. Where a paragraph has a certain grammar, an event has a certain event type. Where a paragraph consists of words, an event consists of properties.

A typical event type may consists of about a dozen properties. When an event type gets much larger than that, it may be trying to tell too much and modelling it properly becomes more complicated. Many data sources already have a data structure that translates naturally into events, such as a row from a database table. Others may require splitting data records into multiple events.

The story of an event is pretty much the answer to the question:

.. epigraph::

  *What does this data mean, exactly?*

In this text we use server logs as an example. We will look into representing logging data from a file server that logs the FTP commands issued by users. We will assume that the log messages have already been parsed into JSON records, one JSON record per message. This might be achieved using some log message processor like LogStash, but this does not really matter for now.

We will assume that each command issued to the server generates one logging message. The question of how to break down the source data into EDXML events is therefore not a very complicated one: We will simply regard the logging messages as the paragraphs that tell the story of our FTP server. This implies that each logging message will result in one EDXML event.

Now suppose that the JSON records are structured like this:

.. code-block:: javascript

   {
     "time":    2016-10-11T21:04:36.167,
     "source":  "/var/log/ftp/command.4234.log",
     "offset":  37873,
     "server":  "192.168.1.20",
     "client":  "192.168.10.43",
     "user":    "alice",
     "command": "quit"
   }

What does this data mean, exactly? In order to answer that question, we need to do a bit of homework. For example, what is the time zone of the ``time`` field in the JSON data? And what is that ``offset`` field all about? Is that ``server`` field always an IP address or can it also contain a host name?

For our example case, we will assume that:

* the ``time`` field is a time specified in UTC
* the ``offset`` and ``source`` fields represent the offset in the original logging file, added by the log forwarder
* the ``server`` and ``client`` fields are always IPv4 addresses

The Event Story
---------------

Now that we understand the data, let us write down the exact meaning of the above JSON record, in plain english:

.. epigraph::

  *On October 11th 2016 at 21:04:36.167h (UTC), a user named 'alice' issued command 'quit' on FTP server 192.168.1.20. The command was issued from a device having IP address 192.168.10.43.*

The above text is called an *event story*. The event story is the very foundation of your data model and writing it down is the most important step in EDXML data modelling. It forces you to think about the exact meaning and significance of your data. In a minute, you will see how this text naturally results in a data model.

There is more to say about the JSON record, but we will get to that later. At this point, we know the story we want to tell and we verified that all the required information is available in the original data.

The Story Template
------------------

Event stories like the one above are closely related to *story templates* in EDXML. For this reason, we will use story templates as the first step towards an EDXML data model for our FTP events. Story templates transform the various event properties into human readable text. The resulting text explains the exact meaning of the event data, in terms of the event properties. Especially if you are just getting started with EDXML data modelling, it is advisable to begin a modelling task by writing down the story template that yields event stories like the one above. Once a satisfactory template has been established, this will also result in a list of required properties, as these are part of the template. Let us convert the above event story into a story template by replacing the variable parts with place holders:

.. epigraph::

  *On [[time]], a user named '[[user]]' issued command '[[command]]' on FTP server [[server]]. The command was issued from a device having IP address [[client]].*

In the above template, we used event properties that have exactly the same names as the fields in the JSON record. We can do that in this case because the JSON records are flat, like EDXML events, and the JSON field names just happen to be valid EDXML property names.

In order to convert the date into something slightly more human friendly, we can use a *string formatter*. Let us use the ``date_time`` formatter to display the time rounded to the nearest second:

.. epigraph::

  *On [[date_time:time,second]], a user named '[[user]]' issued command '[[command]]' on FTP server [[server]]. The command was issued from a device having IP address [[client]].*

.. note::
  The EDXML specification lists a number of string formatters that you can use.

In our example, we assume that all JSON fields are present in every input JSON record. This makes writing down a template quite straight forward. EDXML story templates also supports creating dynamic event stories that change depending on which fields have a value and which do not. Refer to the full specification for details.

The Event Type
--------------

At this point, we have our event story, a story template and we know which properties our EDXML event type will have. It is time to actually define our first event type! We will do so by using the :class:`EventTypeFactory <edxml.ontology.EventTypeFactory>` class. This provides a declarative way to define event types and allows generating a full EDXML ontology from it. Let us begin writing our event type definition, adding just the ``time`` property for now:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v1.py

The EventTypeFactory class offers some constants that we can populate. The ontology will be generated from these constants. The :attr:`TYPES <edxml.ontology.EventTypeFactory.TYPES>` constant simply lists the names of the event types that we want to define. The :attr:`TYPE_PROPERTIES <edxml.ontology.EventTypeFactory.TYPE_PROPERTIES>` constant lists the properties for each event type. It is a dictionary mapping property names to the *object type* of the values that we will store in the property. In this case we use ``GenericBrick.OBJECT_DATETIME``.

The ``GenericBrick.OBJECT_DATETIME`` we use here refers to the definition of an object type from an :doc:`ontology brick <../bricks>`. An ontology brick is a reusable component for building ontologies. By using this object type in stead of defining our own we make sure that our ontology defines time in the same way as other ontologies that also use this ontology brick. This is important, as it makes our ontology compatible with ontologies defined by other EDXML data sources.

.. note::
  The EDXML Foundation maintains a `collection of ontology bricks <https://github.com/edxml/bricks>`_ for this purpose. The definition of the object type we use in our example can be found `here <https://github.com/edxml/bricks/blob/master/generic/index.rst#datetime>`_.

Now, if we want to generate an actual EDXML document containing our ontology, we can use an `EDXML writer <edxml.EDXMLWriter>`_ to do so:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v2.py
  :lines: 2-6

By default the EDXML writer will write the resulting document to standard output. The ontology that we defined so far should result in an EDXML document similar to the one shown below:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v1.edxml
   :language: xml

As you can see the document contains just our event type definition, there is no event data yet. Note that the event type contains a lot more details than we specified. Most of these are defaults of the EDXML implementation in the SDK. Others, like the display names, are brave attempts to guess them based on other information. All of these details can be adjusted by using the constants of the :class:`EventTypeFactory <edxml.ontology.EventTypeFactory>` class.

Let us extend our event type definition a bit more. We can use the :attr:`TYPE_STORIES <edxml.ontology.EventTypeFactory.TYPE_STORIES>` constant to set our story template. And, while we are at it, we also add the remaining properties:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v3.py

Again we used some object types from the public shared brick collection. Our event type also contains one property, ``command``, for which the collection does not offer a fitting object type. For the time being we will use some generic string object type.

Event Uniqueness
----------------

Each EDXML event is uniquely identified by its hash. This hash is computed from its event type, event source and its *hashable properties*. By default none of the properties of an event is hashable. That won't work well because we will produce many different variants of one and the same event. We really need to think about choosing hashable properties.

The question we need to answer now is: What makes an event of our event type truly unique? Of course we could just mark all properties as hashable. But what if a user manages to run the same FTP command multiple times, within the time resolution of the time stamps in the log? Then all of these events will still have the same hash. Machines will consider them as duplicates of a single event. If we want our events to accurately represent the original data, we need to come up with something better.

In the original JSON records we find the name of the log file and the offset of the log message in that file. Let us assume that this combination uniquely identifies a log message. Then we can extend our event type by adding two properties and specify both as hashable:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v4.py

.. note::
  Event hashing is explained in more detail in :doc:`event-hashes`.

Event Order
-----------

The order of events as they appear in an EDXML document has no significance. The event order must be determined by comparing their event properties. When we discussed uniqueness we touched on a potential problem here: The time resolution may not be sufficient to differentiate between log messages produced in quick succession. Not only does this pose a challenge to producing unique events, it also means that the original log message ordering may get lost in translation.

As detailed in the specification the logical event order is determined by comparing time spans and, if that is not sufficient, by subsequently comparing sequence numbers if the event type defines these. In our event type the ``offset`` property looks like a nice candidate for a sequence number. Let us put it to use right away:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v5.py

Concepts
--------

Concepts unlock some of the most powerful features of EDXML, most notably `concept mining <http://edxml.org/concept-mining>`_. Associating properties with concepts and mutually relating those concepts makes your data reach its full potential.

Let us once again ask ourselves a question: Which event properties are identifiers of some concept? To answer that question, we remind ourselves of the analogy of concepts being like the characters in a novel. Concepts are the things that the story is about. The heroes in our story are two computers and a user. Now let us add this information to the event type:

.. code-block:: python

    TYPE_PROPERTY_CONCEPTS = {
        'org.myorganization.logs.ftp': {
            'user': {ComputingBrick.CONCEPT_USER_ACCOUNT: 7},
            'server': {ComputingBrick.CONCEPT_COMPUTER: 8},
            'client': {ComputingBrick.CONCEPT_COMPUTER: 8},
        }
    }

Here we associate event type properties with concepts. And once again we use some concept definitions provided by the public ontology brick collection. In case you are curious what the definition of a computer looks like, you can find it `here <https://github.com/edxml/bricks/blob/master/computing/index.rst#entityphysical-entityobjectwholeartifactinstrumentalitydevicemachinecomputer>`_.

The integer numbers that you see displayed for each concept are *concept confidences*. For the precise definition we refer to the EDXML specification. Long story short: These values are rough indicators of how strong of an identifier the property is for the concept that it is associated with.

The reasoning for choosing the specific values displayed above is as follows. The name of a user account is generally not a very strong identifier because many different unrelated accounts on different computers may share the same account name, like "root" or "admin". We consider the IPv4 address of a computer to be a somewhat stronger identifier because multiple computers having the same IP address is less common.

Choosing confidences is not an exact science. The values are used by concept mining algorithms to *estimate* the confidence of their output.

The next thing to consider is how these concepts relate to one another:

- The user makes use of both the server and the client computer.
- The server serves the client computer

Concept relations are somewhat more complex to express than most aspects of event types. For that reason there are no class constants that we can populate to define them. We need to use the :doc:`../ontology` API for this. The event type factory class uses the :func:`create_event_type() <edxml.ontology.EventTypeFactory.create_event_type>` method to generate its event types. By overriding it we can adjust the event type definitions to our liking. Let us define the relation between the server and client computers:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v6.py
  :lines: 49-54

Here we use an *inter-concept* relation, which indicates that the relation relates two distinct computers rather than linking information about one and the same computer. The relation enables concept mining algorithms to use FTP logs to discover networks of interconnected computers. And, because we used shared ontology bricks, the FTP log events are easily combined with other EDXML data sources which tell us something about the structure of the computer network, about the computers themselves or about their users.

Note that the relation definition also makes use of an EDXML template. This template can be used to translate reasoning steps into English text.

Event Attachments
-----------------

An event type can specify that its events may have attachments. Attachments can be used to supply additional information that supports the story. An attachment can contain many things, ranging from a plain text string to a Base64 encoded picture.

There are some considerations to be made when deciding to store something in a property or in an attachment. As properties are typically part of the event story, long strings or binary strings do not help to keep the event story clear and concise. Attachments do not play any role in concept mining or correlating events. If that is no issue, storing a value as an attachment should be fine.

Let us use an attachment to store the original JSON record along with its resulting event:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_v7.py
  :lines: 49-59

Here we define one attachment with attachment id ``original`` and specify its display name and media type. Note that there is another class constant that can be used to indicate that the attachments are Base64 encoded. In the case of a JSON record the default attachment encoding (plain text) is fine.

Ontology Evolution
------------------

As mentioned before, event types have many more aspects than the ones we have shown here. To keep example code short we left most of these at default values. Omitting details can also be done purposely when designing event types for real. Event types are versioned and *most* of their aspects can be updated later. The emphasis on *most* points us at a critically important step in ontology design:

.. warning::
  Make sure that you correctly specify all immutable aspects in version 1 of your event type.

The main issue is that some aspects of event type definitions cannot be changed after it has been used to generate events. Well, you could do that but that may yield two mutually conflicting event type definitions. The EDXML specification specifies how to update an event type that is guaranteed to work and will be accepted by any EDXML implementation. It also guarantees that events generated using previous versions of their event type are still valid according to newer versions.

To make that happen, some aspects of an event type definition are static. They cannot be changed in newer versions. It is crucial to get these aspects right from the start.

The specification details which aspects of an ontology can be updated and how. In practise, updating an event type involves outputting an ontology containing the updated event type while making sure that the version of the event type is incremented. The EventTypeFactory class has a :attr:`class constant <edxml.ontology.EventTypeFactory.VERSION>` to set the event type version.

Selecting Object Types
----------------------

For the ``command`` property we used a generic string object type. This would work just fine for generating events, it gets the job done. But is also has some consequences that we should consider.

The event type we just defined may not be the only event type using this object type. This may yield surprises when the events are combined with data from other sources that use the same object type for completely different kinds of data. Logged FTP commands may end up on a big pile of object values together with who knows what else.

When two EDXML events refer to the same object value of the same object type, they conceptually share a single object. Correlating events by finding events that share objects is a common thing to do in EDXML data analysis. When a single object can represent two wildly different things, machines may see links between events where there actually is none.

Long story short, it is a good idea to use a more specific object type for representing FTP commands. In doing so we have two options. We can define a `private` object type or a `public` object type. While there is no such thing as a private or public object type in the EDXML specification, it is a useful distinction to make.

**A private object type** is intended to be used by a single EDXML data source. Its name includes a namespace that identifies the data source to make sure that the chances of another data source defining the same object type is minimal. This also implies that object values can never be correlated with events from other data sources and that the objects are not useful for concept mining.

**A public object type** is the opposite. It is intended to be shared among multiple data sources. Its name does not refer to any specific data source. The object values are expected to correlate events from multiple event types or data sources in a meaningful way. And, ideally, it is shared by adding it to the public ontology bricks collection.

Suppose that we decide that finding the exact same FTP command in other event types does not really mean anything to us. Then a private object type is the way to go. We also do not have any concept associated with FTP commands, so we are not missing out on the concept mining end if we use a private object type.

The most convenient way to define our own private object type is to create our own ontology brick:

.. literalinclude:: ../../edxml/examples/edxml_modelling/intro_example_brick.py

We can use this brick in the exact same way as we did with the bricks from the public brick collection. We leave that as an exercise for the reader.

Event Sources
-------------

Every EDXML event has a source. An event source is an URI that provides the means to organize EDXML events in a virtual hierarchy. The position inside this hierarchy represents the origin of the data. For example, event sources may include the name of the data source, or the organization that owns the data. Event sources can also provide a convenient means to filter data. For example, the source might allow filtering data on a specific department within an organization. Including a date in the source URI may be very convenient for implementing data retention policies or efficiently keeping metrics like events per month / week / day.

.. epigraph::

  *Since EDXML source URIs from all data sources combined form a virtual hierarchical tree structure, it is advisable to establish an organization-wide convention for generating source URIs. Document it or, even better, implement it in a shared code library.*

EDXML source URIs should be properly namespaced to prevent any collisions with the URIs produced by another data source. This can be done by including the owner of the data in the URI, as illustrated below:

.. code-block:: text

  /org/myorganization/offices/amsterdam/logs/2021/q2/

Unlike object types and concepts, event sources are usually not shared between data sources. For that reason ontology bricks do not provide the means to define event sources. Defining event sources can be done using the :doc:`ontology API <../ontology>` or using a :doc:`transcoder mediator <../transcoding>`.

EDXML requires outputting the ontology before outputting any events. As event sources are part of the ontology, this suggests that all event sources must be defined upfront. However, EDXML allows outputting ontology updates at any point while producing events, which means that sources can be defined dynamically.

.. epigraph::

  A full working version of the examples shown on this page can be found `on Github <http://github.com/edxml/examples/edxml_modelling/intro_example_full.py>`_.
