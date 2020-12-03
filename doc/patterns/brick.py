# -*- coding: utf-8 -*-

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
