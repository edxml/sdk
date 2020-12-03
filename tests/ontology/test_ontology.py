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

import pytest
from edxml.ontology import Ontology


def test_ontology_versioning():
    ontology = Ontology()

    assert ontology.get_version() == 0

    ontology.create_concept('c')

    assert ontology.is_modified_since(0) is True
    assert ontology.get_version() == 1

    ontology.clear()

    assert ontology.get_version() == 0


def test_ontology_repr():
    ontology = Ontology()
    ontology.create_object_type('o')
    ontology.create_concept('c')
    ontology.create_event_source('/source/')
    ontology.create_event_type('e')

    assert repr(ontology) == '1 event types, 1 object types, 1 sources and 1 concepts'

    ontology.delete_event_type('e')

    assert repr(ontology) == '0 event types, 1 object types, 1 sources and 1 concepts'

    ontology.delete_object_type('o')

    assert repr(ontology) == '0 event types, 0 object types, 1 sources and 1 concepts'

    ontology.delete_event_source('/source/')

    assert repr(ontology) == '0 event types, 0 object types, 0 sources and 1 concepts'

    ontology.delete_concept('c')

    assert repr(ontology) == '0 event types, 0 object types, 0 sources and 0 concepts'


def test_create_duplicate_object_type_fails():
    ontology = Ontology()
    ontology.create_object_type('o')
    with pytest.raises(ValueError):
        ontology.create_object_type('o')


def test_create_duplicate_concept_fails():
    ontology = Ontology()
    ontology.create_concept('c')
    with pytest.raises(ValueError):
        ontology.create_concept('c')


def test_create_duplicate_event_type_fails():
    ontology = Ontology()
    ontology.create_event_type('e')
    with pytest.raises(ValueError):
        ontology.create_event_type('e')


def test_create_duplicate_source_fails():
    ontology = Ontology()
    ontology.create_event_source('/test/')
    with pytest.raises(ValueError):
        ontology.create_event_source('/test/')
