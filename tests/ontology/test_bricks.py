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

from edxml import EventCollection
from edxml.ontology import Brick, Ontology


class TestBrick(Brick):
    @classmethod
    def generate_object_types(cls, target_ontology):
        yield target_ontology.create_object_type('o')

    @classmethod
    def generate_concepts(cls, target_ontology):
        yield target_ontology.create_concept('c')


class DuplicateTestBrick(TestBrick):
    ...


class TestBrickUpgradedObjectType(TestBrick):
    @classmethod
    def generate_object_types(cls, target_ontology):
        yield target_ontology.create_object_type('o').set_version(2)


class TestBrickUpgradedConcept(TestBrick):
    @classmethod
    def generate_concepts(cls, target_ontology):
        yield target_ontology.create_concept('c').set_version(2)


def test_register():
    class TestOntology(Ontology):
        ...

    TestOntology.register_brick(TestBrick)

    ontology = TestOntology()
    event_type = ontology.create_event_type('e')
    event_type.create_property('p', object_type_name='o')

    # Property should now have the object type from the brick
    assert event_type['p'].get_object_type().get_name() == 'o'
    # Ontology should have the concept from the brick
    assert ontology.get_concept('c') is not None


def test_register_duplicate_object_type():
    class TestOntology(Ontology):
        ...

    TestOntology.register_brick(TestBrick)
    with pytest.raises(Exception, match='definition is not identical'):
        # Registering multiple versions of the same ontology element
        # should fail.
        TestOntology.register_brick(TestBrickUpgradedObjectType)


def test_register_duplicate_concept():
    class TestOntology(Ontology):
        ...

    TestOntology.register_brick(TestBrick)
    with pytest.raises(Exception, match='definition is not identical'):
        # Registering multiple versions of the same ontology element
        # should fail.
        TestOntology.register_brick(TestBrickUpgradedConcept)


def test_empty_brick():
    assert list(Brick.generate_object_types(Ontology())) == []
    assert list(Brick.generate_concepts(Ontology())) == []


def test_test():
    TestBrick.test()


def test_dump_edxml():
    edxml = TestBrick.as_xml()

    collection = EventCollection.from_edxml(edxml)

    assert 'o' in collection.ontology.get_object_types()
    assert 'c' in collection.ontology.get_concepts()
