# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

import edxml
from edxml.ontology import Ontology


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
        yield from ()

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
        yield from ()

    @classmethod
    def test(cls):
        """
        This method can be used in unit tests to verify ontology bricks.
        """
        ontology = Ontology()
        object_types = list(cls.generate_object_types(ontology))

        # Check for duplicate object type definitions
        assert len(object_types) == len(ontology.get_object_types())

        # Validate object types
        for object_type in object_types:
            object_type.validate()

        concepts = list(cls.generate_concepts(ontology))

        # Check for duplicate concept definitions
        assert len(concepts) == len(ontology.get_concepts())

        # Validate concepts
        for concept in concepts:
            concept.validate()

    @classmethod
    def as_xml(cls):
        ontology = Ontology()

        list(cls.generate_object_types(ontology))
        list(cls.generate_concepts(ontology))

        return edxml.EDXMLWriter(output=None).add_ontology(ontology).close().flush()
