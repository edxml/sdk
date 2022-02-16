Event Uniqueness & Hashing
==========================

Each EDXML event is uniquely identified by its hash. How this hash is computed is detailed in the `EDXML specification <http://edxml.org/spec>`_. Two events may have differing properties while their hashes are identical. This is due to the fact that an event type may define to only include specific properties while computing its hash: The *hashable properties*.

When two physical events share the same hash, they are instances of one and the same logical event. The physical events are said to collide and can be merged together. This characteristic gives events a unique and persistent identifier. The event can be referred to by its hash even as it evolves over time.

Generating colliding events allows an event source to produce an update for a previously generated event. A recipient can merge the events to track the current state of some variable record in the source. A typical example is representing tickets from a ticketing system that have a variable status ('open', 'in progress', 'done').

Defining hashable properties can be done by using the :func:`make_hashed() <edxml.ontology.EventProperty.make_hashed()>` method on the event property:

.. code-block:: python

  my_event_type.create_property('time', 'datetime').make_hashed()

Multiple instances of the same logical event can be merged using the various merge strategies defined in the EDXML specification. By default, the merge strategy of all properties is set to ``any``. Setting a different merge strategy on an event property can be done using the various ``merge_...()`` methods on the property. A quick example:

.. code-block:: python

  my_event_type['time-end'].merge_max()

Choosing hashable properties
----------------------------

Choosing which properties to include in the hash is a critical step in event type design. It determines if and how events can evolve. It shows what makes an event unique. It has a role in defining :doc:`parent-child relations <parents-children>` between event types. Updating the set of hashable properties for a particular event type is not possible, you must get it right from the start. Well, you can do it but this yields two conflicting definitions of the same event type.

Some data sources already produce unique persistent identifiers for their data records like a UUID or a hash. In that case, you are lucky: All that needs to be done is storing this unique identifier in an event property and marking it as the only hashable property. Problem solved. However, there is another aspect of event uniqueness to consider here: Semantics. Using that UUID from the data source to uniquely identify your EDXML events will work perfectly, but the resulting events will not convey what it really is that makes them unique.

Let us clarify the semantics problem by looking at an example. Consider a data source yielding records that contain address information comprising of a postal code and a house number. The data source produces exactly one record for each unique address. Each record also contains a unique database record identifier. Modelling an event type to represent these records could be done by using the database identifiers provided by the source for uniqueness. However, the fact that the combination of postal code and house number makes each event unique will be lost. Data analysis algorithms can no longer infer what makes these events unique by inspecting the event type definition. By marking the two properties that contain the postal code and the house number as hashable in stead, the semantics of the event type are much stronger.
