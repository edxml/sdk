Modelling Hierarchical Structures
=================================

EDXML events have a simple, flat structure. While this flat structure has many advantages, it also poses some challenges. When modelling data from sources that produce nested data structures like JSON or XML, the original data records typically need to be broken up into multiple EDXML events. The original hierarchical structure gets lost in the process. As a result, it becomes difficult to grasp the relationships between the various types of events.

In EDXML, modelling of nested data structures is done by defining parent-child relations between event types. These definitions enable machines to aggregate multiple events into hierarchical structures as desired.

Before we look at how we can use the SDK to define parent / child relationships, let us recap the `EDXML specification <http://edxml.org/spec>`_ on the subject. Parent and child events have the following characteristics:

- A parent event can identify all of its children in terms of its own properties
- A child event can identify its parent in terms of its own properties
- A child event has at most one parent
- The parent-child relationship cannot be broken by updating parent or child

This is only possible when:

1. The parent event type defines at least one hashed property
2. The child event contains a copy of all hashed properties of the parent
3. The properties that the child shares with the parent cannot be updated

As an example, suppose that we wish to model a directory of files stored on a computer. We define one event type ``dir`` describing the directory itself, which may contain a hashed property ``name`` containing the directory name and possibly some aggregate information like the total number of files it contains. Then we define another event type ``file`` describing a file contained in the directory. The file event type contains a property ``dir`` containing the name of the directory that contains the file.

.. epigraph::

  *Refer to* :doc:`this document<event-hashes>` *to learn about defining hashed properties*

Defining parent / child relations
---------------------------------

Now we can express the parent-child relationship between both event types as follows:

.. code-block:: python

    file.make_child('contained in', dir.make_parent('containing', file)).map('dir', 'name')

The API to define the relationship is defined to yield code that is actually quite readable. In plain English, it says:

.. epigraph::

  *Make a file into a child contained in the directory, which is the parent containing the file, by mapping the directory of the file to the name of the directory.*

Note that the text fragments 'contained in' and 'containing' are more than just syntactic sugar. These texts are in fact the parent description and siblings description that the EDXML specification is talking about. The call to :func:`make_child() <edxml.ontology.EventType.make_child()>` returns an instance of the :class:`edxml.ontology.EventTypeParent` class. The call to :func:`map() <edxml.ontology.EventTypeParent.map()>` creates the property map. As detailed in the EDXML specification, the property map defines which object values are shared between the parent and child events and which property of the child corresponds with each of the properties of the parent event.

  *It may be convenient to match the names of the properties that bind the parent and child event types. In that case, the second argument to the map() method can be omitted.*

Parent / child relations can also be defined in a declarative way when using an :doc:`event type factory <../event_type_factory>` or a :doc:`transcoder <../transcoding>`. The following example illustrates what this might look like:

.. literalinclude:: ../../edxml/examples/define_parent_declarative.py
  :language: Python
