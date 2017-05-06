EDXML Event Representations
===========================

Since EDXML is all about events, there is a rich set of classes for representing EDXML events in the SDK. The simplest one is the EDXMLEvent_ class. It implements a `MutableMapping <https://docs.python.org/2/library/collections.html>`_ for convenient access to event properties.

The EDXMLEvent_ class has two subclasses which are typically used far more often than the base class. The first one is the ParsedEvent_ class. As the name suggests, this class is instantiated by EDXML parsers and its objects are a mix between a regular EDXMLEvent_ and a `etree.Element <http://lxml.de/tutorial.html#the-element-class>`_ instance. The reason for a separate parsed event variant is performance: The lxml library can generate these objects at minimal cost and can be passed through to EDXML writers for re-serialization at minimal cost.

The second subclass of EDXMLEvent_ is EventElement_. This class is a wrapper around a lxml ``etree.Element`` instance containing an ``<event>`` XML element, providing the same convenient access interface as its parent, EDXMLEvent_. The EventElement_ is mainly used for generating events that are intended for feeding to EDXML writers.

- EDXMLEvent_
- ParsedEvent_
- EventElement_

edxml.EDXMLEvent
----------------
.. _EDXMLEvent:

.. autoclass:: edxml.EDXMLEvent
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.ParsedEvent
-----------------
.. _ParsedEvent:

.. autoclass:: edxml.ParsedEvent
    :special-members: __init__
    :members:
    :show-inheritance:

edxml.EventElement
------------------
.. _EventElement:

.. autoclass:: edxml.EventElement
    :special-members: __init__
    :members:
    :show-inheritance:
