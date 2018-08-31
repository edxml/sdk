# -*- coding: utf-8 -*-


class Brick(object):
    """
    Class representing an ontology brick. Ontology bricks contain definitions
    of object types and concepts. By defining these in ontology bricks, the
    definitions can be shared and installed using standard Python package
    management tools.

    Using ontology bricks simplifies the process of producing and maintaining
    collections of tools that generate mutually compatible EDXML data streams,
    by sharing ontology element definitions in the form of Python modules.

    Ontology bricks should extend this class and override the generate methods
    that create the ontology elements.
    """

    @classmethod
    def generate_object_types(cls, target_ontology):
        """

        Creates any object types that are defined by the
        brick using specified ontology, yielding each
        of the created ObjectType instances.

        Args:
          target_ontology (edxml.ontology.Ontology): The ontology to add to

        Yields:
          List[edxml.ontology.ObjectType]:

        """
        return
        yield

    @classmethod
    def generate_concepts(cls, target_ontology):
        """

        Creates any concepts that are defined by the
        brick using specified ontology, yielding each
        of the created Concept instances.

        Args:
          target_ontology (edxml.ontology.Ontology): The ontology to add to

        Yields:
          List[edxml.ontology.Concept]:

        """
        return
        yield
