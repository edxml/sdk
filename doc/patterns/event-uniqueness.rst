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

Choosing unique properties
--------------------------

Choosing which event properties should uniquely identify an event is a fundamental choice in designing an event type. Some data sources already produce unique persistent identifiers for their data records like a UUID or a hash. In that case, you are lucky: All that needs to be done is storing this unique identifier in an event property and marking it as unique. Problem solved. However, there is another aspect of event uniqueness to consider here: Semantics. Using that UUID from the datasource to uniquely identify your EDXML events will work perfectly, but the resulting events will not convey what it is that makes them unique.

Let us clarify the semantics problem by looking at an example. Consider a data source yielding records that contain address information comprising of a postal code and a house number. The data source produces exactly one record for each unique address. Each record also contains a unique identifier computed from the combination of postal code and house number. Modelling an event type to represent these records could be done by using the identifiers provided by the source for uniqueness. However, the fact that the combination of postal code and house number makes each event unique will be lost. Data analysis algorithms can no longer infer what makes these events unique by inspecting the event type definition. By marking the two properties that contain the postal code and the house number as unique in stead, the semantics of the event type are much stronger.

The unique identifier provided by the data source can be safely omitted from the event type when a unique property combination is used in stead. When you are unsure if the property combination is sufficient to unique identify the events, the source provided identifier can be kept as one of the unique properties of the event type. It is better to have some redundancy than to risk events getting merged when they should not be.
