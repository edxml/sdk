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
from edxml.ontology import Brick, Ontology


def test_event_type_factory():
    class TestBrick(Brick):
        @classmethod
        def generate_object_types(cls, target_ontology):
            yield target_ontology.create_object_type('my.object.type')

    Ontology.register_brick(TestBrick)

    from edxml.examples import event_type_factory  # noqa: