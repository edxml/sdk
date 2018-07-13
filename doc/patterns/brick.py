# -*- coding: utf-8 -*-
import edxml


class ExampleBrick(edxml.ontology.Brick):
    """
    Example brick that defines one concept.
    """

    CONCEPT_COMPUTER = 'computer'

    @classmethod
    def generate_concepts(cls, target_ontology):
        yield target_ontology.create_concept('computer') \
            .set_description('some kind of a computing device') \
            .set_display_name('computer')


edxml.ontology.Ontology.register_brick(ExampleBrick)
