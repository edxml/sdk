Event Type Factories
====================

Apart from procedurally defining ontology elements it is also possible to define them in a declarative fashion. This is done by defining a class that extends :class:`EventTypeFactory <edxml.ontology.EventTypeFactory>`. This class defines a set of class constants that can be populated to describe one or more event types. These event types can then be generated from these class constants.

A quick example to illustrate:

.. literalinclude:: ../edxml/examples/event_type_factory.py
  :language: Python

The EventTypeFactory class is also the base of the :class:`RecordTranscoder <edxml.transcode.RecordTranscoder>` class and its extensions. These classes combine ontology generation with event generation and are the most convenient way to generate EDXML data.

Of course there are many more class constants that can be used to create more complex ontologies. These can be found in the below class documentation.

edxml.ontology.EventTypeFactory
-------------------------------
.. _`event type_factory`:
.. _EventTypeFactory:

.. autoclass:: edxml.ontology.EventTypeFactory
    :members:
    :show-inheritance:


