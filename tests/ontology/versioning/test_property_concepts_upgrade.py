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

"""
Test to verify that updates to property relation definitions
work as expected. Contrary to test_event_type_property_relation_upgrade, these
tests check comparing and updating of isolated relation definitions.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable, assert_invalid_ontology_upgrade


def test_copies_are_identical():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    e = o.create_event_type('a')
    e.create_property('a', 'a')
    e.create_property('b', 'a')
    a = e['a'].identifies('a')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_different_concept_associations_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')
    o.create_concept('b')

    e = o.create_event_type('a')
    p = e.create_property('p1', 'a')
    p.identifies('a')
    p.identifies('b')

    a = p.get_concept_associations()['a']
    b = p.get_concept_associations()['b']

    # Comparing two different concept associations
    # makes no sense and throws an exception.
    assert_incomparable(a, b)


def test_associations_from_different_event_types_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a').identifies('a')

    e2 = o.create_event_type('b')
    e2.create_property('a', 'a').identifies('a')

    a = e1['a'].get_concept_associations()['a']
    b = e2['a'].get_concept_associations()['a']

    # Comparing two associations from different event types
    # makes no sense and throws an exception.
    assert_invalid_ontology_upgrade(a, b)


def test_associations_with_different_properties_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a').identifies('a')
    e1.create_property('b', 'a').identifies('a')

    a = e1['a'].get_concept_associations()['a']
    b = e1['b'].get_concept_associations()['a']

    # Comparing two associations with different properties
    # makes no sense and throws an exception.
    assert_invalid_ontology_upgrade(a, b)


def test_remove_concept_not_allowed():

    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')
    o.create_concept('b')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a')

    # An attempt to upgrade to a version missing the
    # concept association must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_change_associated_concept_not_allowed():

    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')
    o.create_concept('b')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a')
    b['a'].identifies('b')

    # An attempt to upgrade to a version having a different
    # concept association must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_change_attribute_name_extension_not_allowed():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a').set_attribute('a', display_name_singular='a')
    b['a'].identifies('a').set_attribute('b', display_name_singular='b')

    # An attempt to upgrade to a version having a different
    # concept attribute name extension must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_add_concept_association():

    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')
    o.create_concept('b')

    a = o.create_event_type('a')
    a.create_property('a', 'a')
    a['a'].identifies('a')

    b = copy.deepcopy(a).set_version(2)

    b['a'].identifies('b')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_confidence_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a').set_confidence(1)
    b['a'].identifies('a').set_confidence(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_confidence_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We change the confidence without incrementing the version.
    b = copy.deepcopy(a)

    a['a'].identifies('a').set_confidence(1)
    b['a'].identifies('a').set_confidence(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_cnp_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a').set_concept_naming_priority(1)
    b['a'].identifies('a').set_concept_naming_priority(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_cnp_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We change the CNP without incrementing the version.
    b = copy.deepcopy(a)

    a['a'].identifies('a').set_concept_naming_priority(1)
    b['a'].identifies('a').set_concept_naming_priority(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_display_name_upgrade_singular():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a').set_attribute('a', display_name_singular='a', display_name_plural='a')
    b['a'].identifies('a').set_attribute('a', display_name_singular='b', display_name_plural='a')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_display_name_upgrade_singular():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We change the display name without incrementing the version.
    b = copy.deepcopy(a)

    a['a'].identifies('a').set_attribute('a', display_name_singular='a', display_name_plural='a')
    b['a'].identifies('a').set_attribute('a', display_name_singular='b', display_name_plural='a')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_display_name_upgrade_plural():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].identifies('a').set_attribute('a', display_name_singular='a', display_name_plural='a')
    b['a'].identifies('a').set_attribute('a', display_name_singular='a', display_name_plural='b')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_display_name_upgrade_plural():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We change the display name without incrementing the version.
    b = copy.deepcopy(a)

    a['a'].identifies('a').set_attribute('a', display_name_singular='a', display_name_plural='a')
    b['a'].identifies('a').set_attribute('a', display_name_singular='a', display_name_plural='b')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_change_inherited_object_type_display_name():
    o1 = Ontology()
    o2 = Ontology()

    # Create two versions of the object type with differing display names,
    # each in its own ontology.
    o1.create_object_type('a', display_name_singular='s', display_name_plural='p').set_version(1)
    o2.create_object_type('a', display_name_singular='s2', display_name_plural='p2').set_version(2)

    # Now create identically defined event types in both ontologies. The
    # only difference is the object type of the property. The concept attribute
    # has no custom display name, so it inherits the display name from the
    # object type. Yet, the difference in object types does *not* mean that the
    # event types are now different.
    o1.create_concept('a')
    o2.create_concept('a')

    a = o1.create_event_type('a')
    a.create_property('a', 'a')

    b = o2.create_event_type('a')
    b.create_property('a', 'a')

    a['a'].identifies('a')
    b['a'].identifies('a')

    # Both event types should still be considered equal.
    assert a == b


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
