Ontology Bricks
===============

Ontology bricks are EDXML ontology element definitions wrapped in a Python class. As such, they can be shared, distributed as installable Python modules. This facilitates sharing ontology elements between multiple projects, which is especially useful for developing multiple EDXML data sources that generate mutually compatible ontologies.

Ontology bricks are designed for sharing object type definitions and concept definitions, because these are the only ontology elements for which it makes sense to share them. A simple import of an ontology brick is sufficient to make them available to the Ontology class. Definitions from an imported ontology brick will be automatically added to any Ontology instance that you create, on demand. For example, when an event type definition is added to an Ontology instance, any missing object types and concepts that the event type refers to will be looked up in the imported bricks. Any object types and concepts that are provided by the bricks will be automatically added to your Ontology instance.

.. epigraph::

  *Besides sharing ontology elements, defining bricks is an elegant way to define 'private' object types and concepts that you intend to use locally in your EDXML generator.*

In order to make the automatic addition of brick elements work, the Python source file that defines the brick must contain a call to :func:`edxml.ontology.Ontology.RegisterBrick` to register itself with the Ontology class. For example, if your brick class is named MyBrick, the source file must contain the command::

  edxml.ontology.Ontology.RegisterBrick(MyBrick)

Creating an ontology brick is done by extending the :class:`edxml.ontology.Brick` class and overriding one or two methods. Below, we show a full example of a brick which defines one concept:

.. literalinclude:: brick.py

Note the use of a class constant. This allows code that uses the concept to refer to its name in an indirect way. Should you ever want to rename the concept, there is only one line of code that needs to be changed.

