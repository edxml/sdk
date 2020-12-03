import pytest
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
