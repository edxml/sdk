Generating Event Collisions
===========================

As explained in the EDXML specification, each EDXML event is uniquely identified by its *sticky hash*. By default, all event information is included in the hash. As a result, any change to the event yields a new event.

By including *unique properties* in your event type definitions, the way these hashes are computed changes. The event is now uniquely identified by its type, source and unique properties. Other event information is ignored. This means that multiple, physically different events can actually represent the same logical event, because their sticky hashes are identical. By using unique properties, you can purposely generate hash collisions between events, allowing them to be merged.

Generating colliding events allows an event source to produce an update for a previously generated event. A recipient can merge the events to track the current state of some variable record in the source. Typical examples are tickets from a ticketing system that have a variable status ('open', 'in progress', 'done'). Or a source might compute some incremental aggregate that is constantly being updated. Defining unique properties is also required in order to define :doc:`parent-child relationships<parents-children>` between event types.

Creating unique properties can be done by calling the :func:`edxml.ontology.EventProperty.unique()` method on the event property:

.. code-block:: python

  my_event_type.create_property('time', 'datetime').unique()

Multiple instances of the same logical event can be merged using the various merge strategies defined in the EDXML specification. By default, the merge strategy of all properties is set to ``drop``. Setting a different merge strategy on an event property can be done using the various ``merge_...()`` methods on the property. A quick example:

.. code-block:: python

  my_event_type['time-end'].merge_max()

