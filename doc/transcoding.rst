Data Transcoding
================

EDXML data is most commonly generated from some type of input data. The input data is used to generate output events. The EDXML SDK features the concept of a *record transcoder*, which is a class that contains all required information and logic for transcoding a chunk of input data into an output event. The SDK can use record transcoders to generate events and event type definitions for you. It also facilitates unit testing of record transcoders.

In case the input data transforms into events of more than one event type, the transcoding process can be done my multiple record transcoders. This allows splitting the problem of transcoding the input in multiple parts. A *transcoder mediator* can be used to automatically route chunks of input data to the correct transcoder.

A record transcoder is an extension of the :doc:`EventTypeFactory <event_type_factory>` class. Because of this, record transcoders use class constants to describe event types. These class constants will be used to populate the output ontology while transcoding.

All record transcoders feature a :attr:`TYPE_MAP <edxml.transcode.RecordTranscoder.TYPE_MAP>` constant which maps record selectors to event types. Record selectors identify chunks of input data that should transcode into a specific type of output event. What these selectors look like depends on the type of input data.

Object Transcoding
------------------

The most generically usable record transcoder is the :class:`ObjectTranscoder <edxml.transcode.object.ObjectTranscoder>` class. Below example illustrates its use:

.. literalinclude:: ../edxml/examples/transcoder_object.py
  :language: Python

This example does not show the use of a mediator, we directly use a single transcoder here. In case of the object transcoder, the record selector is actually the name of type of input record. What happens when the :func:`edxml.transcode.object.generate()` method is called is the following. The transcoder will check the :attr:`TYPE_MAP <edxml.transcode.RecordTranscoder.TYPE_MAP>` constant and see that an input record of type ``user`` should yield an output event of type ``test-event-type``. It will then instantiate an event of that type and start populating its properties. It checks the :attr:`TYPE_MAP <edxml.transcode.RecordTranscoder.PROPERTY_MAP>` constant to see which record fields it should read and which property its values should be stored in. In this example, the ``name`` field goes into the ``user.name`` property.

Next, the transcoder needs to read the ``name`` field from the input record. We say "field" here because we did not specify what ``name`` refers to. It might be the name of an attribute of the input record. Or the record might be a dictionary and ``name`` is a key in that dictionary. The transcoder will first try to treat the record as a dictionary and use its ``get()`` method to read the ``name`` item. In our example, the record is not a dictionary and the read will fail. Then, the transcoder will try to see if the record has an attribute named ``name`` by attempting to read it using the ``getattr()`` method. This will succeed and the output event property is populated.

As we mentioned before, the ``name`` value in the :attr:`PROPERTY_MAP <edxml.transcode.RecordTranscoder.PROPERTY_MAP>` constant is not just a name. It is a selector. As such, it can point to more than just dictionary entries or attributes in input records. You can use a dotted syntax to address values within values. For example, ``foo.bar`` can be used to access an item named ``bar`` inside a dictionary named ``foo``. And if ``bar`` happens to be a list, you can address the first entry in that list by using ``foo.bar.0`` as selector.

The resulting events are not written into EDXML output yet. We will extend the example to include a transcoder mediator, which will yield something more useful:

.. literalinclude:: ../edxml/examples/transcoder_object_mediator.py
  :language: Python

Now we see that the :attr:`TYPE_FIELD <edxml.transcode.RecordTranscoder.TYPE_FIELD>` constant of the mediator is used to set the name of the field in the input records that contains the record type. The example uses a single type of input record named `user`. The record transcoder is registered with the mediator using the same record type name. When the record is fed to the mediator using the :func:`edxml.transcode.RecordTranscoder.process` method the mediator will read the record type and use the associated transcoder to generate an output event. In this case the output EDXML stream will be written to standard output. Note that the transcoder produces binary data, so we write the output to ``sys.stdout.buffer`` rather than ``sys.stdout``.

XML Transcoding
---------------

When you need to transcode XML input you can use the :class:`XMLTranscoder <edxml.transcode.object.XMLTranscoder>` class. It is highly similar to the :class:`ObjectTranscoder <edxml.transcode.object.ObjectTranscoder>` class. The main difference is in how input records and fields are identified. This is done using XPath expressions. Below example illustrates this:

.. literalinclude:: ../edxml/examples/transcoder_xml_mediator.py
  :language: Python

Note the use of XPath expressions in the above example. Firstly, the transcoder is registered to transcode all XML elements that are found using XPath expression ``users``. These will be treated as input records for the transcoding process. In our example, only the element at location ``users/user`` will be found and fed to the transcoder. Second, the :attr:`TYPE_MAP <edxml.transcode.RecordTranscoder.TYPE_MAP>` constant indicates that any XML element matching XPath expression ``user`` should be used as input record for outputting an event of type ``test-event-type``. Finally, the :attr:`PROPERTY_MAP <edxml.transcode.RecordTranscoder.PROPERTY_MAP>` constant indicates that the event property named ``user.name`` should be populated by applying XPath expression ``name`` to the input record. This ultimately results in a single output event containing object value ``Alice``.

Outputting Multiple Events
--------------------------

By default, the transcoding process produces a single EDXML output event for each input data record. When input records contain a lot of information it may make sense to transcode a single input record into multiple output events. This can be achieved by overriding the :func:`post_process() <edxml.transcode.RecordTranscoder.post_process>` function. This function is actually a generator taking a single EDXML event as input and generating zero or more output events. The input record from which the event was constructed is provided as a function argument as well.

Unit Testing
------------

Record transcoders can be tested using a transcoder test harness. This is a special kind of transcoder mediator. There is the :class:`TranscoderTestHarness <edxml.transcode.TranscoderTestHarness>` base class and the :class:`ObjectTranscoderTestHarness <edxml.transcode.object.ObjectTranscoderTestHarness>` and :class:`XmlTranscoderTestHarness <edxml.transcode.xml.XmlTranscoderTestHarness>` extensions. Feeding input records into these mediators will have the test harness use your transcoder to generate an EDXML document containing the output ontology and events, validating the output in the process. The EDXML document will then be parsed back into Python objects. The data is validated again in the process. Finally, any colliding events will be merged and the final event collection will be validated a third time. This assures that the output of the transcoder can be serialized into EDXML, deserialized and merged correctly.

After feeding the input records the parsed ontology and events are exposed by means of the :attr:`events <edxml.transcode.TranscoderTestHarness>` attribute of the test harness. This attribute is an :class:`EventCollection <edxml.EventCollection>` which you can use to write assertions about the resulting ontology and events. So, provided you feed the test harness with a good set of test records, this results in unit tests that cover everything. The transcoding process itself, ontology generation, validity of the output events and event merging logic.

A quick example of the use of a test harness is shown below:

.. literalinclude:: ../edxml/examples/transcoder_harness.py
  :language: Python

Automatic Data Normalization and Cleaning
-----------------------------------------

Data sources can be challenging at times. Values may not be in a form that fits into the EDXML data type. Or a single field may contain data of varying data types. Or a value may contain downright nonsensical gibberish. Transcoders feature various means of dealing with these challenges. Input data can be automatically normalized and cleaned.

By default the transcoding process will error when a transcoder outputs an event that contains an invalid object value. A common case is date / time values. There are so many different formats for representing time, and EDXML accepts just one specific format. In stead of adding code to properly normalize all time data in your transcoders, you can also have the SDK do the normalization for you. In order to do so you can use the :attr:`TYPE_AUTO_REPAIR_NORMALIZE <edxml.transcode.RecordTranscoder.TYPE_AUTO_REPAIR_NORMALIZE>` constant to opt into automatic normalization for a particular event property.

Note that automatic normalization also allows for using non-string values in output events. For example, placing a float in a property that uses an EDXML data type from the decimal family will normalize that float into a decimal string representation that fits the data type. Some of the supported Python types are float, bool, datetime, Decimal and IP (from `IPy <https://pypi.org/project/IPy/>`_).

In some cases, input data may contain values that are outside of the value space of the data type of the output event property. Using the :attr:`TYPE_AUTO_REPAIR_DROP <edxml.transcode.RecordTranscoder.TYPE_AUTO_REPAIR_DROP>` constant it is possible to opt into dropping these values from the output event. A common case is an input record that contains a field that may hold both IPv4 and IPv6 internet addresses. In EDXML these must be represented using different data types and separate event properties. This can be done by having the transcoder store the value in both properties. This means that one of the two properties will always contain an invalid value. By allowing these invalid values to be dropped, the output events will always have the values in the correct event property.

Note that there is quite a performance penalty for enabling automatic normalization and cleaning. In many cases, this will not matter much. In case performance turns out to be an issue, you can always optimize your transcoder by normalizing event objects yourself. You might find the :attr:`TYPE_PROPERTY_POST_PROCESSORS <edxml.transcode.RecordTranscoder.TYPE_PROPERTY_POST_PROCESSORS>` constant helpful. Alternatively, you can override the :func:`post_process() <edxml.transcode.RecordTranscoder.post_process>` function to modify the autogenerated events as needed.

In case you want to retain the original record values as they were before normalization and cleaning there are two options for doing so. Firstly, the original value could be stored in another property and an 'original' relations could be used to relate the original value to the normalized one. Second, (part of) the original input record could be stored as an event attachment.

Description & Visualization
---------------------------

The `Transcoder Mediator`_ class contains two methods that allows EDXML transcoders to generate descriptions and visualizations of their output ontology. Both can be great aids to review the ontology information in your record transcoders. The first of these methods is :func:`describe_transcoder() <edxml.transcode.TranscoderMediator.describe_transcoder>`, which is a shortcut to :func:`describe_producer_rst() <edxml.ontology.description.describe_producer_rst>`. Refer to that method for details. The other method is :func:`generate_graphviz_concept_relations() <edxml.transcode.TranscoderMediator.generate_graphviz_concept_relations>`, which is a shortcut to :func:`generate_graph_property_concepts() <edxml.ontology.visualization.generate_graph_property_concepts>`. Again, refer to that method for details.

API Documentation
-----------------

Below, the documentation of the various transcoding classes is given.

*Base Classes*

- `Record Transcoder`_
- `Transcoder Mediator`_
- `Transcoder Test Harness`_

*Transcoders & Mediators*

- `Object Transcoder`_
- `Object Transcoder Mediator`_
- `XML Transcoder`_
- `XML Transcoder Mediator`_

*Test Harnesses*

- `Object Transcoder Test Harness`_
- `XML Transcoder Test Harness`_

RecordTranscoder
^^^^^^^^^^^^^^^^
.. _`Record Transcoder`:

.. autoclass:: edxml.transcode.RecordTranscoder
    :members:
    :show-inheritance:

TranscoderMediator
^^^^^^^^^^^^^^^^^^
.. _`Transcoder Mediator`:

.. autoclass:: edxml.transcode.TranscoderMediator
    :members:
    :show-inheritance:

TranscoderTestHarness
^^^^^^^^^^^^^^^^^^^^^
.. _`Transcoder Test Harness`:

.. autoclass:: edxml.transcode.TranscoderTestHarness
    :members:
    :show-inheritance:

ObjectTranscoder
^^^^^^^^^^^^^^^^
.. _`Object Transcoder`:

.. autoclass:: edxml.transcode.object.ObjectTranscoder
    :members:
    :show-inheritance:

ObjectTranscoderMediator
^^^^^^^^^^^^^^^^^^^^^^^^
.. _`Object Transcoder Mediator`:

.. autoclass:: edxml.transcode.object.ObjectTranscoderMediator
    :members:
    :show-inheritance:

XmlTranscoder
^^^^^^^^^^^^^
.. _`XML Transcoder`:

.. autoclass:: edxml.transcode.xml.XmlTranscoder
    :members:
    :show-inheritance:

XmlTranscoderMediator
^^^^^^^^^^^^^^^^^^^^^
.. _`XML Transcoder Mediator`:

.. autoclass:: edxml.transcode.xml.XmlTranscoderMediator
    :members:
    :show-inheritance:

ObjectTranscoderTestHarness
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. _`Object Transcoder Test Harness`:

.. autoclass:: edxml.transcode.object.ObjectTranscoderTestHarness
    :members:
    :show-inheritance:

XmlTranscoderTestHarness
^^^^^^^^^^^^^^^^^^^^^^^^
.. _`XML Transcoder Test Harness`:

.. autoclass:: edxml.transcode.xml.XmlTranscoderTestHarness
    :members:
    :show-inheritance:
