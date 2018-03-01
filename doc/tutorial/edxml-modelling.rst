EDXML Data Modelling
====================

.. epigraph::

  *This tutorial assumes that the reader is familiar with the EDXML specification.*

Every data source has a story to tell. This tutorial will show how to write a simple wrapper around a single data source, allowing it to tell its story. Such wrappers are called *EDXML transcoders*. As an example, we will consider the case of an FTP server that logs all FTP commands issued by users, like a user downloading a file for instance. In 10 steps, we will write a fully functional transcoder that produces EDXML events along with detailed semantics.

Step 1 - Understand your Data
-----------------------------

One of the first questions to be answered when modelling data as EDXML events is: How can the original data be broken down into EDXML events? To answer that question, it may be helpful to think of EDXML events as stories. Every single EDXML event represents a little story, told by the data source to any other EDXML enabled system that wants to hear about it. The story of the event is pretty much the answer to the question:

.. epigraph::

  *What does this data mean, exactly?*

Since EDXML uses events to represent data, the data will be modeled in terms of events, which form the basic structure of the EDXML data. Each event consists of properties, which in turn refer to object types and concepts. This implies that the data source must yield data that features a record-like structure. This may be a database outputting table rows, an API outputting JSON data, a stored XML file containing XML elements, or some other type of structured data.

Unstructured data requires some form of pre-processing in order to model it in EDXML. In our example, we will assume that logging data from an FTP server has been preprocessed to yield a stream of JSON records, one JSON record per line. This might be achieved using some log message processor like LogStash, but this does not really matter for now.

In our example, we will assume that each command issued to the FTP server generates one logging message. The question of how to break down the source data into EDXML events is therefore not a very complicated one: We will simply regard each of the logging messages as the stories, which implies that our transcoder will output one EDXML event for each logging message that it receives on its input.

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

What is the story told by this JSON record? Recall what we said previously about the stories: The story is the answer to the question: What does this data mean, exactly? In order to answer that question, we need to do a bit of homework. For example, what is the time zone of the ``time`` field in the JSON data? And what is that ``offset`` field all about? Is that ``server`` field always an IP address or can it also contain a host name? We might need to consult some documentation, look at configuration files of the data source and possibly ask the guy who configured the FileBeat log forwarder for instance.

For our example case, we will assume that:

* the ``time`` field is a time specified in UTC
* the ``offset`` and ``source`` fields represent the offset in the original logging file, added by the log forwarder
* the ``server`` and ``client`` fields are always IPv4 addresses

Step 2: Write the Event Story
-----------------------------

Now that we understand the data, let us write down the exact meaning of the above JSON record, in plain english:

.. epigraph::

  *On October 11th 2016 at 21:04:36.167h (UTC), a user named 'alice' issued command 'quit' on FTP server 192.168.1.20. The command was issued from a device having IP address 192.168.10.43.*

The above text is called an *event story*. The event story is the very foundation of your data model and writing it down is the most important step in EDXML data modelling. It forces you to think about the exact meaning and significance of your data upfront. This may seem tedious at first, especially if you are used to just cram a bunch of JSON into Elastic Search and be done with it. However, if you intend to do anything useful with your data other than putting some pie charts on the screen, enriching the data with semantics allows for more powerful and easier analysis further down the road: Computers better understand your data and can be more helpful analysing it as a result. In stead of the analyst getting tired explaining the computer how the data 'works' all day, the computer can tirelessly explain the analyst how the data works.

Back to our event story. As you can see, we decided not to tell anything about the log forwarding. Our imaginary IT department maintains a very short retention policy on the logs, so the ``offset`` and ``source`` fields loose their meaning pretty quickly. Deciding which data from the original data source is significant for the event story is an integral part of each data modelling process.

.. epigraph::

  *The data structure in this tutorial is quite simple and allows for a simple one-on-one relationship between the input data records and output EDXML events. In general, things may be more complicated. A single source may produce multiple types of data records, each of which having a different associated event story. Handling such composite data sources is covered* :doc:`here <../patterns/composed-sources>`.

There is more to say about the JSON record, but we will get to that later. At this point, we know the story we want to tell and we verified that all the required information is available in the original data.

Step 3: Write the Story Template
---------------------------------

Event stories like the one above are closely related to *story templates* in EDXML. For this reason, we will use story templates as the first step towards an EDXML data model for our FTP events. In the EDXML specification, event stories are templates that transform the various event properties into human readable text. The resulting text explains the exact meaning of the event data, in terms of the event properties. Especially if you are just getting started with EDXML data modelling, it is advisable to begin a modelling task by writing down the story template that yields event stories like the one above. Once a satisfactory template has been established, this will also result in a list of required properties, as these are part of the template. Let us convert the above event story into a story template by replacing the variable bits with place holders:

.. epigraph::

  *On [[FULLDATETIME:time]], a user named '[[user]]' issued command '[[command]]' on FTP server [[server]]. The command was issued from a device having IP address [[client]].*

In the above template, we used event properties that have exactly the same names as the fields in the JSON record. We can do that in this case because the JSON records are flat, like EDXML events, and the JSON field names just happen to be valid EDXML property names. In order to convert the date into something slightly more human friendly, we used a formatter for the time field.

In our example, we assume that all JSON fields are present in every input JSON record. This makes writing down a template quite straight forward. When the input data contains optional data elements, things will be more complicated.

Step 4: Define the Event Type
-----------------------------

At this point, we have our event story, a story template and we know which properties our EDXML event type will have. Time to write some code! Let us begin by creating a new, empty EDXML ontology:

.. literalinclude:: example1.py
   :lines: 1-3

Now we can use this ontology to define our own event type, which represents the FTP logging messages:

.. literalinclude:: example1.py
   :lines: 28-35

There are a few things to note about the event type definition. First of all, the SDK offers what is called a *fluid interface*, allowing to write short code that is easy to read. Then the even type name. For reasons pointed out in the EDXML specification, we use the dotted structure to create a private namespace for ourselves. We added the story template that we wrote down earlier, as well as a summary template, which is just a shortened variant of the story template.

Next, let's add the event properties:

.. literalinclude:: example1.py
   :lines: 37-41

Above, we associated each property with an EDXML object type. Remember the difference between properties and object types from the EDXML specification: An object type is globally unique and groups values that represent *the same type of information*. An event property exists only within a single event type and provides context for an object type. Our event type contains two IPv4 addresses sharing a single object type, once in the context of an FTP client and once in the context of an FTP server.

.. epigraph::

  *Note that we did not consider event uniqueness here: for simplicity, we did not define any unique properties. Sticky hashes are computed from all event properties, which implies that our FTP event type cannot have children and cannot be updated. In our example, this is fine. The events that we produce do not track any kind of state and there is no hierarchy of event types involved. In some cases, it may be useful to explicitly define* :doc:`event uniqueness<../patterns/event-uniqueness>` *or create* :doc:`parent / child relationships<../patterns/parents-children>`.

How to Choose Object Types
--------------------------

When assigning object types to properties, you should carefully consider when to assign different object types to properties and when to assign the same object type to multiple properties. To do so, remember how object types are defined in the EDXML specification. Object types are meant to indicate when two object values from two different events should be considered identical. Identical objects can be shared between events. Events that share objects are building blocks for constructing graphs by connecting events through their shared objects. This changes your data set from a pile of loose data fragments into an implicitly structured graph.

Apart from implicitly structuring a set of events, object types also allow object values to be validated because we specify what the values should look like. Also, databases can optimize their table structure and queries if they know what to expect from the values of a particular object type. For example, some databases can save 70% storage capacity if they know that the values they need to store only contain characters from the latin-1 character set. However if you use a latin-1 object type, the first time your transcoder attempts to output a unicode string for that same object type, it will throw a validation exception. So be specific, but not too specific.

Those are the most important things to consider when deciding which object type to use for your event properties. In case you are still in doubt, a 'rules of thumb' can be applied to make your decision. Consider two properties A and B. Both properties share some object type X. For each property, write down 10 arbitrary but realistic values. Now shuffle all values from both properties. Is it still possible to tell which value belongs to which property? If yes, it probably makes sense to use different object types for each property. Or the other way around: Consider two properties A and B associated with two different object types X and Y. For each property, write down 10 arbitrary but realistic values. Now shuffle all values from both properties. Is it impossible to tell which value belongs to which property? If so, it probably makes sense to use the same object type for both properties.

Step 5: Define the Object Types
-------------------------------

So far we have not defined any object types yet, so running the code from the preceding step will make the SDK complain about undefined object types. However, by defining the event type properties first, we established which object types we need. This is why it is useful to define properties first and define the required object types later.

.. epigraph::

  *In the code, the object type definitions must precede the event type definitions!*

Let us add some object type definitions then, starting out with the 'datetime' object type:

.. literalinclude:: example1.py
   :lines: 7-10

.. epigraph::

  *Since object types are often shared between multiple EDXML data sources, it is not common practise to explicitly define all required object types inline. We do that here for educational purposes. Normally, object types are imported from an* :doc:`Ontology Brick <../patterns/ontology-bricks>`.

The above code for creating the 'datetime' object type is pretty straight forward. A nice fluid interface is showing itself. Note the use of the :class:`edxml.ontology.DataType` class to create an EDXML data type. This class has methods for creating any data type supported by the EDXML specification. As you can see, the description of the object type is pretty verbose. It is important to be precise here. Object type definitions are typically shared and re-used elsewhere, so people should know exactly what the object type is intended to be used for and what their values should look like. In this case of an EDXML `datetime` value, there is not much to worry about because the EDXML specification prescribes its format *exactly*. In general, there is more freedom in the values accepted by a particular object type, so be sure not to leave your object type definition open for too much freedom of interpretation.

On to the next object type:

.. literalinclude:: example1.py
   :lines: 12-15

Here, take note of the display name. Both a singular and plural form is provided in this case. By default, the SDK will 'guess' the plural form by adding an 's' to the singular form, which would obviously not work here.

One more:

.. literalinclude:: example1.py
   :lines: 17-21

Here, note the argument used to set the maximum string length of the string data type. We specify it here for two reasons. First of all, it is a sanity check. In this example, we decided that we want this object type to only accept values that have a reasonable length. If some really, really long user name is written into an event, an error should result. The last method call sets a fuzzy matching hint on the object type, as detailed in the EDXML specification.

Lastly, we define the object type representing FTP commands:

.. literalinclude:: example1.py
   :lines: 23-26

Step 6: Add an Event Source
---------------------------

Event sources provide the means to organize EDXML events in a hierarchy representing the origin of the data. For example, event sources may include the name of the organizational unit. This allows for filtering on events that have the same type but originate from different departments. Including the date in the source URI may be very convenient for implementing data retention policies or efficiently keeping metrics like events per month / week / day.

.. epigraph::

  *Since EDXML source URIs from all data sources combined form a virtual hierarchical tree structure, it is advisable to establish an organization-wide convention for generating source URIs. Document it or, even better, implement it in a shared code library.*

EDXML source URIs must be globally unique, in the sense that two EDXML data sources generating events having the (partially) identical source URI end up in the same part of the global virtual tree structure. Be sure to create a source URI name space for your organization to prevent URI collisions should you ever wish to exchange information with third parties.

Let us add an event source definition to our ontology:

.. literalinclude:: example1.py
   :lines: 43

.. epigraph::

  *For simplicity, we generate a single static source for all output events. In practise, it may be desirable to dynamically assign source URIs to output events. This can be done as explained* :doc:`here <../patterns/dynamic-edxml-sources>`.


Step 7: Producing Events
------------------------

At this point, we have covered the minimum that is required to construct a fully working EDXML data model. Time to produce some events! We do that by instantiating a :class:`edxml.SimpleEDXMLWriter`, injecting our ontology and setting its default output event type and source:

.. literalinclude:: example1.py
   :lines: 45-51

And then, the actual event generation loop. We just read lines from standard input and parse each of them as JSON. Then, we delete the two JSON fields that we decided to omit from the EDXML events. We also need to take care to generate valid object values. In this example, we use the :func:`edxml.ontology.DataType.FormatUtcDateTime` method to produce valid EDXML datetime strings. And finally, we create an event and write it. The resulting write loop looks like this:

.. literalinclude:: example1.py
   :lines: 53-66

The example code lacks any error handling, we leave it as an exercise to the reader to add it. But wait, we just forgot the one thing that everybody forgets all the time:

.. literalinclude:: example1.py
   :lines: 68

This call finalizes the EDXML output stream. We need to explicitly close the output stream in this case because we did not use a Python context. Luckily, the :class:`edxml.SimpleEDXMLWriter` class features a context manager that we can use to prevent us from having to explicitly close the output stream. Using Python's :keyword:`with` keyword, we can rewrite the event writing loop to look like this:

.. literalinclude:: example1b.py
   :lines: 48-58

All combined, this is what we got so far:

.. literalinclude:: example1b.py

Step 8: Define Property Relations
---------------------------------

As we mentioned before, all ingredients of a complete, valid EDXML generator have been covered. The resulting events fully convey the event story that we started out with. Still, *we did not tell the full story*. There are aspects about the story that human readers will infer from the text. Let us refer back to our event story again:

.. epigraph::

  *On October 11th 2016 at 21:04:36.167h (UTC), a user named 'alice' issued command 'quit' on FTP server 192.168.1.20. The command was issued from a device having IP address 192.168.10.43.*

From this text we might infer that, apparently, Alice has access to FTP server 192.168.1.20 because she issued a command on that server. We can also infer that the two network devices 192.168.1.20 and 192.168.10.43 communicated with each other. To us humans, these inferred facts are so obvious and natural that we automatically infer things from texts, without realising it. For computers, this inference is not natural at all, let alone automatic. Using EDXML, we can help the poor machines a little by providing additional semantics in the form of *property relations*. Before we dive in and add property relations to our event type definition, let us briefly touch upon the significance of these inferred relations. Why is it useful to enable computers to know about these relations? There are a few different use cases:

**Querying**
  When our data set contains relations describing users that have access to IP addresses, no matter which data sources these relations originate from, we can ask the computer who is known to have access to a specific IP address. The computer can then answer the question by combining all events of all event types that contain the relation.
**Graph Analysis**
  Relations can be used to generate a graph from a set of EDXML events. Graphs can be `visualized and analyzed <https://gephi.org/>`_, expanding the toolset of analysts.
**Concept Mining**
  Actually a special form of graph analysis, which deserves special mention. Property relations that relate properties that refer to concepts are required to make EDXML concept mining possible. Please refer to the EDXML specification for details about concept mining and the role of property relations in concept mining.

There may be many, many possible property relations that one can define for a given event type. Relations are implicit in EDXML, so adding relations does not add to the size and storage requirements of the EDXML events. Still, having many relations in an event type can be confusing. Also, when the relations are materialized into a graph, for example using a graph database, having too many relations is an effective way to produce spaghetti graphs. Therefore it is useful to consider the above use cases and decide which relations are actually useful.

Having said that, let us now have a look at defining property relations. Remember how property relations are defined in the EDXML specification. They are not defined as part of the events themselves. Much like how humans infer relations from the context of the information, EDXML processing machines infer relations from the event type that provides the context for a given event. Property relations are part of the event type definition.

 .. code-block:: python

  myEventType['user'].RelateTo('has access to', 'server')\
    .Because('a user named [[user]] issued a command on FTP server [[server]]')

There you have it. You can almost read it like a normal English sentence. The ``RelateTo()`` method creates and returns the actual relation between properties ``user`` and ``server``, using predicate ``has access to``. Then, the reason of the relation is set. This string is a template string, similar to the event story templates we started out with. It is another little story, answering the question:

  `Why are these two values related?`

These 'relation stories' are useful to analysts studying the structure of a data set. For example, when graph analysis yields a relation between event object A and E via objects B, C and D, the computer can combine the relation stories to explain why A and E are related, in plain English. The computer can even provide an estimate of how confident it is found the relation it found if you, the data model designer, provide another hint: Relation confidence. Let us extend the above example to provide relation confidence:

 .. code-block:: python

  myEventType['user'].RelateTo('has access to', 'server')\
    .Because('a user named [[user]] issued a command on FTP server [[server]]')\
    .SetConfidence(10)

In this case, we actually don't need to specify confidence, because confidence is set to ``10`` by default. In using this confidence value, we assumed that each input record represents a command that can only be issued by users that have access permission to the FTP server.

The assigned confidence could have been different in case this assumption could not be made. For example, suppose that a failed login attempt would also result in a the same type of input record. In that case we could have used a slightly lower confidence, like ``9``, to indicate that the relation as stated might in fact not be true. This is important, because confidence is used both by human analysts and analysis algorithms to estimate the accuracy of analysis results.

Step 9: Define Concepts
-----------------------

When discussing property relations, we briefly mentioned EDXML concepts. Concepts, as explained in the EDXML specification, pop up in three different stages in EDXML modelling:

1. Defining the concept itself
2. Defining concept properties
3. Defining relations between concept properties

Let us work through all three stages and apply them to our FTP example. First, we define the concept of a computer:

 .. code-block:: python

    myOntology.CreateConcept('computer')\
              .SetDescription('some kind of a computing device')\
              .SetDisplayName('computer')

Pretty straight forward and similar to defining object types. Next, we adjust the ``client`` and ``server`` property definitions to refer to the computer concept:

 .. code-block:: python

    myEventType['client'].Identifies('computer', 9)
    myEventType['server'].Identifies('computer', 9)

In the above code, we assigned an identification confidence of ``9``. This confidence value indicates how strong of an identifier the property is for the concept. Since it is possible for two different computers to have the same IPv4 address, we chose not to stick with the default of ``10`` and set a slightly lower value. Similar to property relation confidences, this is a hint that both human analysts and computer algorithms can use to assess the accuracy of analysis results.

.. epigraph::

  *The exact value of the confidence is a bit arbitrary, it has no scientific base or anything. If we chose a value of 8 we would not have expected to obtain wildly different analysis results.*

Lastly, concept properties can (and should!) be related using property relations. The EDXML specification mentions two different types of concept relations: inter-concept and intra-concept. Let us express the fact that the client and server IP addresses belong to two distinct computers that are related:

 .. code-block:: python

  myEventType['client'].RelateIntra('communicates with', 'server')\
    .Because('[[client]] connected to FTP server [[server]]')

The only difference between a 'regular' property relation and an intra-concept or inter-concept relation is the name of the method used to create it. Using the semantics we expressed above, computers can use FTP records to construct network graphs showing how multiple computers are wired together.

.. epigraph::

  *Astute readers might note that, in theory, the client and the server can in fact be the same computer and that one computer can have multiple IP addresses. To these readers we apologise for the fact that we choose to keep things simple here and for the fact that the data model is, well, just a model. Reality is always more complex. For that, we also apologise.*

Step 10: Adding Event Content
-----------------------------

Besides property objects, events may also contain event content. Event content is basically just a free form UTF-8 text string that is devoid of the limitations that apply to event properties. It can be used to store potentially long strings that could otherwise 'blow up' the event story template when it is evaluated.

Event content is also frequently used to store the original input data that was used to produce the event. Besides its obvious use for reproducing the original data set from the EDXML data, there is another interesting use case This allows for for re-generating an EDXML data set using an updated version of the transcoder. When an EDXML transcoder supports reading input data from, say, a logging file *or* from a previously generated EDXML data file, the transcoder will be able to upgrade EDXML data sets that were produced by older versions of itself. This is particularly useful when :doc:`transcoding composed data sources <../patterns/composed-sources>` using a transcoder that gradually supports a greater set of input record types with each new version.

Adding content to an event is simple: Just invoke its :func:`edxml.EDXMLEvent.SetContent()` method and pass it a UTF-8 string. In our FTP example, we will store the original logging message in each output event:

.. code-block:: python

  writer.AddEvent(EDXMLEvent(properties).SetContent(line))

After adding property relations, concepts and event content, the full source code for our final EDXML transcoder now looks like this:

.. literalinclude:: example1c.py

