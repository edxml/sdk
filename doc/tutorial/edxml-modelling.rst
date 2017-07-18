EDXML Data Modelling
====================

Every data source has a story to tell. This tutorial we will show how to write a simple wrapper around a single data source, allowing it to tell its story. As an example, we will consider the case of an FTP server that logs all FTP commands issued by users, like a user downloading a file for instance.

Step 1 - Understand your Data
=============================

One of the first questions to be answered when modelling data into EDXML events is: How can the original data be broken down into EDXML events? To answer that question, it may be helpful to think of EDXML events as stories. Every single EDXML event represents a little story, told by the data source that produces the EDXML data to any other EDXML enabled system that wants to hear about it. The story of the event is pretty much the answer to the question:

.. epigraph::

  *What does this data mean, exactly?*

Since EDXML uses events to represent data, the data will be modeled in terms of events, which form the basic structure of the EDXML data. Each event consists of properties, which in turn refer to object types. This implies that the data source must yield data that features a record-like structure. This may be a database, an API outputting JSON data, a stored XML file, or some other type of structured data.

Unstructured data requires some form of pre-processing in order to model it in EDXML. In our example, we will assume that the logging data from the FTP server has been preprocessed to yield a stream of JSON records, one JSON record per line. This might be achieved using some logging data processor like LogStash, but this does not really matter for now.

In our example, we will assume that each command issued to the FTP server generates one logging message. The question of how to break down the source data into EDXML events is therefore not a very complicated one: We will simply regard each of the logging messages as the stories, which implies that our wrapper will produce one output EDXML event for each logging message that it receives on its input.

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

* the time field is in UTC
* the ``offset`` and ``source`` fields represent the offset in the original logging file, added by the log forwarder
* the ``server`` and ``client`` fields are always IPv4 addresses

Step 2: Write the Event Story
=============================

Now that we understand the data, let us write down the exact meaning of the above JSON record, in plain english:

.. epigraph::

  *On October 11th 2016 at 21:04:36.167h (UTC), a user named 'alice' issued command 'quit' on FTP server 192.168.1.20. The command was issued from a device having IP address 192.168.10.43.*

The above text is called an *event story*. The event story is the very foundation of your data model and writing it down is the most important step in EDXML data modelling. It forces you to think about the exact meaning and significance of your data upfront. This may seem tedious at first, especially if you are used to just cram a bunch of JSON into Elastic Search and be done with it. However, if you intend to do anything useful with your data other than putting some pie charts on the screen, enriching the data with semantics allows for more powerful and easier analysis further down the road: Computers better understand your data and can be more helpful analysing it as a result. In stead of the analyst getting tired explaining the computer how the data 'works' all day, the computer can tirelessly explain the analyst how the data works.

Back to our event story. As you can see, we decided not to tell anything about the log forwarding. Our imaginary IT department maintains a very short retention policy on the logs, so the ``offset`` and ``source`` fields loose their meaning pretty quickly. Deciding which data from the original data source is significant for the event story is an integral part of each data modelling process.

.. epigraph::

  *The data structure in this tutorial is quite simple and allows a simple one-on-one relationship between the input data records and output EDXML events. In general, things may be more complicated. A single source may produce multiple types of data records, each of which having a different associated event story. Handling such composite data sources is covered* :doc:`here <../patterns/composed-sources>`.

There is more to say about the JSON record, but we will get to that later. At this point, we know the story we want to tell and we verified that all the required information is available in the original data.

Step 3: Write the Reporter String
=================================

Event stories like the one above are closely related to *reporter strings* in EDXML. For this reason, we will use reporter strings as the first step towards an EDXML data model for our FTP events. As detailed in the EDXML specification, reporter strings are templates that transform the various event properties into human readable text. The resulting text explains the exact meaning of the event data, in terms of the event properties. Especially if you are just getting started with EDXML data modelling, it is advisable to begin a modelling task by writing down the reporter strings that yield event stories like the one above. Once a satisfactory reporter string has been established, this will also result in a list of required properties, as these are part of the reporter string. Let us convert the above event story into an EDXML reporter string by replacing the variable bits with place holders:

.. epigraph::

  *On [[FULLDATETIME:time]], a user named '[[user]]' issued command '[[command]]' on FTP server [[server]]. The command was issued from a device having IP address [[client]].*

In the above reporter string, we used event properties that have exactly the same names as the fields in the JSON record. This is possible because the JSON records are flat, like EDXML events, and the JSON field names just happen to be valid EDXML property names. In order to convert the date into something slightly more human friendly, we used a formatter for the time field.

In our example, we assume that all JSON fields are present in every input JSON record. This makes writing down a reporter string quite straight forward. When the input data contains optional data elements, things will be more complicated.

Step 4: Define the Event Type
=============================

At this point, we have our event story, a reporter string and we know which properties our EDXML event type will have. Time to write some code! Let us begin by creating a new, empty EDXML ontology:

.. literalinclude:: example1.py
   :lines: 1-3

Now we can use this ontology to define our own event type, which represents the FTP logging messages:

.. literalinclude:: example1.py
   :lines: 28-35

There are a few things to note about the event type definition. First of all, the SDK offers what is called a *fluid interface*, allowing to write short code that is easy to read. Then the even type name. For reasons pointed out in the EDXML specification, we use the dotted structure to create a private namespace for ourselves. We added the reporter string that we wrote down earlier, as well as a short variant.

Next, let's add the event properties:

.. literalinclude:: example1.py
   :lines: 37-41

Above, we associated each property with an EDXML object type. Remember the difference between properties and object types from the EDXML specification: An object type is globally unique and groups values that represent *the same type of information*. An event property exists only within a single event type and provides context for an object type. Our event type contains two IPv4 addresses sharing a single object type, once in the context of an FTP client and once in the context of an FTP server.

We have not defined any object types, so running the above code will make it complain about undefined object types. However, by defining the event type properties now, we established which object types we need. This is why it is useful to define properties first and define the required object types later.

.. epigraph::

  *In the code, the object type definitions must precede the event type definitions!*

Step 5: Define the Object Types
===============================

Let us add some object type definitions then, starting out with the 'datetime' object type:

.. literalinclude:: example1.py
   :lines: 7-10

.. epigraph::

  *Since object types are often shared between multiple EDXML data sources, it is not common practise to explicitly define all required object types inline. We do that here for educational purposes. Normally, object types are imported from an* :doc:`Ontology Brick <../patterns/ontology-bricks>`.

Step 4: Add an Event Source
===========================

Event sources provide the means to organize EDXML events in a hierarchy representing the origin of the data. For example, event sources may include the name of the organizational unit. This allows for filtering on events that have the same type but originate from different departments. Including the date in the source URI may be very convenient for implementing data retention policies or efficiently keeping metrics like events per month / week / day.

.. epigraph::

  *Since EDXML source URIs from all data sources combined form a virtual hierarchical tree structure, it is advisable to establish an organization-wide convention for generating source URIs. Document it or, even better, implement it in a shared code library.*

EDXML source URIs must be globally unique, in the sense that two EDXML data sources generating events having the (partially) identical source URI end up in the same part of the global virtual tree structure. Be sure to create a source URI name space for your organization to prevent URI collisions should you ever wish to exchange information with third parties.

  *to be continued...*
