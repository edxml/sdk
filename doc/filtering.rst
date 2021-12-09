Filtering EDXML Data
====================

A common task in EDXML event processing is filtering. When filtering data streams, the input is parsed, the parsed events and ontology are manipulated and re-serialized to the output. For this purpose the EDXML SDK features filtering classes. These classes are extensions of EDXML parsers that contain an EDXMLWriter instance to pass the parsed data through into the output. By subclassing one of the provided filtering classes, you can creep in between the parser and writer to alter the data in transit.

Using the filtering classes is best suited for tasks where the output ontology will be identical or highly similar to the input ontology. Some possible applications are:

- Deleting events from the input
- Deleting an event type (ontology and event data)
- Obfuscating sensitive data in input events
- Compressing the input by merging colliding events

Like with the parser classes, there is both a `push filter`_ and a `pull filter`_, extending the push parser and pull parser respectively. In order to alter input data, the callback methods of the parser should be overridden. Then, the parent method can be called with a modified instance of the data that was passed to it.

Referencing Events
------------------

When storing references to parsed events you will notice that the events will each have their own EDXML namespace rather than inheriting from the root element. This is caused by the parser dereferencing the events after parsing, detaching them from the root element. To prevent that from happening the :func:`copy() <edxml.EDXMLEvent.copy>` method can be used to store a copy of the event in stead.

Class Documentation
-------------------

The class documentation can be found below.

- EDXMLFilterBase_
- EDXMLPushFilter_
- EDXMLPullFilter_

edxml.EDXMLFilterBase
^^^^^^^^^^^^^^^^^^^^^
.. _EDXMLFilterBase:

.. autoclass:: edxml.EDXMLFilterBase
    :members:
    :show-inheritance:
    :private-members:

edxml.EDXMLPushFilter
^^^^^^^^^^^^^^^^^^^^^
.. _EDXMLPushFilter:
.. _`push filter`:

.. autoclass:: edxml.EDXMLPushFilter
    :members:
    :show-inheritance:

edxml.EDXMLPullFilter
^^^^^^^^^^^^^^^^^^^^^
.. _EDXMLPullFilter:
.. _`pull filter`:

.. autoclass:: edxml.EDXMLPullFilter
    :members:
    :show-inheritance:
