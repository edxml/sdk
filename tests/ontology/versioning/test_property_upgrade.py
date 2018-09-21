"""
Test to verify that updates to event type property definitions
work as expected. Contrary to test_event_type_properties_upgrade, these
tests check comparing and updating of isolated property definitions.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable


def test_different_properties_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    e = o.create_event_type('a')
    a = e.create_property('a', 'a')
    b = e.create_property('b', 'a')

    # Comparing two properties with different names
    # makes no sense and throws an exception.
    with pytest.raises(Exception):
        a > b


def test_properties_of_different_event_types_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a').create_property('a', 'a')
    b = o.create_event_type('b').create_property('a', 'a')

    # Comparing two properties with different names
    # makes no sense and throws an exception.
    with pytest.raises(Exception):
        a > b


def test_copies_are_identical():
    o = Ontology()
    o.create_object_type('a')

    e = o.create_event_type('a')
    a = e.create_property('a', 'a')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_description_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_description('changed')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_description_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We change the description without incrementing the version.
    b = copy.deepcopy(a)
    b['a'].set_description('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_similar_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')
    b = copy.deepcopy(a).set_version(2)
    b['a'].hint_similar('changed')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_similar_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We change the similarity hint without incrementing the version.
    b = copy.deepcopy(a)
    b['a'].hint_similar('changed')

    assert_incomparable(a, b)


def test_single_valued_to_multi_valued_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').set_multi_valued(False)
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_multi_valued(True)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_single_valued_to_multi_valued_upgrade_not_allowed():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').set_multi_valued(True)
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_multi_valued(False)

    # Single-valued properties can become multi-valued, while a multi-valued
    # property cannot become single-valued. The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_mandatory_to_optional_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').set_optional(False)
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_optional(True)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_mandatory_to_optional_upgrade_not_allowed():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').set_optional(True)
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_optional(False)

    # Mandatory properties can become optional, while a optional
    # property cannot become mandatory. The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_confidence_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').identifies('some.concept', 1)
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_concept_confidence(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_confidence_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').identifies('some.concept', 1)

    # We change the concept confidence hint without incrementing the version.
    b = copy.deepcopy(a)
    b['a'].set_concept_confidence(2)

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_concept_naming_priority_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').identifies('some.concept', 1).set_concept_naming_priority(1)
    b = copy.deepcopy(a).set_version(2)
    b['a'].set_concept_naming_priority(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_concept_naming_priority_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').identifies('some.concept', 1).set_concept_naming_priority(1)

    # We change the concept naming priority without incrementing the version.
    b = copy.deepcopy(a)
    b['a'].set_concept_naming_priority(2)

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_object_type_upgrade_not_allowed():
    o1 = Ontology()
    o1.create_object_type('a')
    o1.create_object_type('b')

    o2 = copy.deepcopy(o1)

    a = o1.create_event_type('a')
    a.create_property('a', 'a')

    b = o2.create_event_type('a').set_version(2)
    b.create_property('a', 'b')

    # Property object types differ, the versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_set_concept_not_allowed():
    o1 = Ontology()
    o1.create_object_type('a')
    o1.create_concept('a')

    o2 = copy.deepcopy(o1)

    a = o1.create_event_type('a')
    a.create_property('a', 'a')

    b = o2.create_event_type('a').set_version(2)
    b.create_property('a', 'a').identifies('a', 1)

    # New property has a concept association while the old one did not,
    # the versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_change_concept_not_allowed():
    o1 = Ontology()
    o1.create_object_type('a')
    o1.create_concept('a')
    o1.create_concept('b')

    o2 = copy.deepcopy(o1)

    a = o1.create_event_type('a')
    a.create_property('a', 'a').identifies('a', 1)

    b = o2.create_event_type('a').set_version(2)
    b.create_property('a', 'a').identifies('b', 1)

    # New property is associated with a different concept than the old one,
    # the versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_change_merge_strategy_not_allowed():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a').merge_min()

    # We make a newer event type in which the merge strategy has changed.
    b = copy.deepcopy(a).set_version(2)
    b['a'].merge_max()

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_change_uniqueness_not_allowed():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')

    # We make a newer event type in which the property has become unique.
    b = copy.deepcopy(a).set_version(2)
    b['a'].unique()

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
