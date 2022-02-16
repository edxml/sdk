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

def test_event_type_factory():
    from edxml.examples.define_parent_declarative import FileSystemTypes

    class TestFactory(FileSystemTypes):
        def create_object_types(self, ontology):
            ontology.create_object_type('filesystem-name')

    ontology = TestFactory().generate_ontology()
    ontology.validate()

    assert ontology.get_event_type('file').get_parent() is not None
