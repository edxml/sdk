"""
Test to verify that fluent upgrades of object types and concepts as done
in ontology bricks works as expected.
"""

import pytest

from edxml.error import EDXMLValidationError
from edxml.ontology import Ontology, DataType


def test_valid_object_type_upgrade():
    o = Ontology()
    object_type = o.create_object_type('a')

    assert object_type.get_description() == 'a'
    assert object_type.get_version() == 1

    object_type.set_description('changed').upgrade()

    assert object_type.get_description() == 'changed'
    assert object_type.get_version() == 2


def test_invalid_object_type_upgrade():
    o = Ontology()
    with pytest.raises(EDXMLValidationError):
        # Changing the data type should fail.
        o.create_object_type('a').set_data_type(DataType.boolean()).upgrade()


def test_valid_concept_upgrade():
    o = Ontology()
    concept = o.create_concept('a')

    assert concept.get_description() == 'a'
    assert concept.get_version() == 1

    concept.set_description('changed').upgrade()

    assert concept.get_description() == 'changed'
    assert concept.get_version() == 2

# Note that we do not test invalid concept upgrades as concepts
# have no methods that can produce backward incompatible changes.
