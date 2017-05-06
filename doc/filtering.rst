Filtering EDXML Data Streams
============================

A common task in EDXML event processing is filtering. When filtering data streams, the input is parsed, the parsed events and ontology are manipulated and re-serialized to the output. For this purpose the EDXML SDK features filtering classes, which are extensions of EDXML parsers that contain an EDXMLWriter instance to pass the parsed data through into the output. By subclassing one of the provided filtering classes, you can creep in between the parser and writer to alter the data in transit.

Using the filtering classes is best suited for tasks where the output ontology will be identical or highly similar to the input ontology. Some possible applications are:

- Deleting events from the input
- Deleting an event type (ontology and event data)
- Obfuscating sensitive data in input events
- Compressing the input by merging colliding events

Like with the parser classes, there is both a `push filter`_ and a `pull filter`_, extending the push parser and pull parser respectively. In order to alter input data, the callback methods of the parser should be overridden. Then, the parent method can be called with a modified instance of the data that was passed to it.

- EDXMLFilter_
- EDXMLPushFilter_
- EDXMLPullFilter_

edxml.EDXMLFilter
-----------------
.. _EDXMLFilter:

.. autoclass:: edxml.EDXMLFilter
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EDXMLPushFilter
---------------------
.. _EDXMLPushFilter:
.. _`push filter`:

.. autoclass:: edxml.EDXMLPushFilter
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EDXMLPullFilter
---------------------
.. _EDXMLPullFilter:
.. _`pull filter`:

.. autoclass:: edxml.EDXMLPullFilter
    :special-members: __init__
    :members:
    :show-inheritance:
