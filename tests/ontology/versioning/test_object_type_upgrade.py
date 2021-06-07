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


def test_compression_hint_upgrade():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).compress().set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_xref_upgrade():

    o = Ontology()
    a = o.create_object_type('a', data_type=DataType.float().type)
    b = copy.deepcopy(a).set_xref('http://foo.bar').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_unit_upgrade():

    o = Ontology()
    a = o.create_object_type('a', data_type=DataType.float().type)
    b = copy.deepcopy(a).set_unit('meters', 'm').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_radix_upgrade():

    o = Ontology()
    a = o.create_object_type('a', data_type=DataType.float().type).set_unit('meters', 'm')
    b = copy.deepcopy(a).set_prefix_radix(2).set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_regex_soft_upgrade():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).set_regex_soft(r'[\s\S]*|[a-z]').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_regex_soft_upgrade():

    o = Ontology()
    a = o.create_object_type('a')

    # We change the soft regex without incrementing the version.
    b = copy.deepcopy(a).set_regex_soft(r'[\s\S]*|[a-z]')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_set_hard_regex_fails():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).set_regex_hard(r'[\s\S]*|[a-z]').set_version(2)

    # Setting a previously unset regular expression is not allowed
    # and makes both versions incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_extend_hard_regex():

    o = Ontology()
    a = o.create_object_type('a').set_regex_hard(r'[a-z]')
    b = copy.deepcopy(a).set_regex_hard(r'[a-z]|[A-Z]').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_invalid_hard_regex_upgrade_fails():

    o = Ontology()
    a = o.create_object_type('a').set_regex_hard(r'[a-z]')
    b = copy.deepcopy(a).set_regex_hard(r'[a-z][A-Z]').set_version(2)

    # Changing the regular expression in this way is not allowed
    # and makes both versions incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_fuzzy_matching_upgrade():

    o = Ontology()
    a = o.create_object_type('a')
    b = copy.deepcopy(a).fuzzy_match_phonetic().set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


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
