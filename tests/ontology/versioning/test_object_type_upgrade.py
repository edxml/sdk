import copy
import pytest

from edxml.ontology import Ontology, DataType
from tests.assertions import assert_valid_upgrade, assert_invalid_ontology_upgrade


def test_different_object_types_cannot_be_compared():
    o = Ontology()
    a = o.create_object_type('a')
    b = o.create_object_type('b')

    # Comparing two object types with different names
    # makes no sense and throws an exception.
    with pytest.raises(Exception):
        a == b


def test_copies_are_identical():
    o = Ontology()
    a = o.create_object_type('a')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_description_upgrade():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).set_description('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_description_upgrade():

    o = Ontology()
    a = o.create_object_type('a')

    # We change the description without incrementing the version.
    b = copy.deepcopy(a).set_description('changed')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_display_name_upgrade():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).set_display_name('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_display_name_upgrade():

    o = Ontology()
    a = o.create_object_type('a')

    # We change the display name without incrementing the version.
    b = copy.deepcopy(a).set_display_name('changed')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_compression_hint_upgrade_fails():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).compress().set_version(2)

    # Changing the compression hint is not allowed and makes both
    # versions incompatible, the cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_regex_upgrade_fails():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).set_regexp(r'changed').set_version(2)

    # Changing the regular expression is not allowed and makes both
    # versions incompatible, the cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_fuzzy_matching_upgrade_fails():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).fuzzy_match_phonetic().set_version(2)

    # Changing the fuzzy matching hint is not allowed and makes both
    # versions incompatible, the cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_data_type_upgrade_fails():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).set_data_type(DataType.boolean()).set_version(2)

    # Changing the data type is not allowed and makes both
    # versions incompatible, the cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
