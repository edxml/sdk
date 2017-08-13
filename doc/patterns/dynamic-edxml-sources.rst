Generating Dynamic Source URIs
==============================

A commonly encountered problem is generating EDXML source URIs based on the events that are generated. For example, an EDXML transcoder might want to generate source URIs containing the month of the time stamps in the output events. When the input data is transcoded in a streaming fashion the event timestamps are not known in advance, which implies that the EDXML sources cannot be defined upfront.

The problem may also pop up in EDXML processors which read streaming EDXML data, process it and output a new EDXML data stream. The processor might want to place the processed events in a sub-branch of the virtual EDXML source tree relative to the URI of the input events, such that an input event having source URI

  `/my/organization/data/`

results in an output event having source URI

  `/my/organization/data/processed/`

Again, the source URIs of the input events are unknown in advance, to the output URIs cannot be defined upfront.

When using the :class:`edxml.SimpleEDXMLWriter` class to produce output events, it is possible to change the ontology while generating the events. This class will track the ontology for changes and automatically outputs the ontology updates while producing events. A code snippet illustrating this is shown below.

.. literalinclude:: dynamic-edxml-source.py

In the above example code, we can see that the event write loop defines a new EDXML event source just before outputting an event. Note that a list is kept containing previously defined sources, allowing it to define a new source only when needed. This is just done for efficiency, defining the same event source multiple times is not a problem.
