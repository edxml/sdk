"""
Test to verify that updates to event type parent definitions
work as expected. Contrary to test_event_type_parent_upgrade, these
tests check comparing and updating of isolated parent definitions.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable


def test_copies_are_identical():
    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    parent.create_property('a', 'a').unique()
    child = o.create_event_type('child')
    child.create_property('a', 'a').set_multi_valued(False)

    a = child.make_children('of', parent.is_parent('of', child))
    b = copy.deepcopy(a)

    # Exact copies should be identical.
    assert a == b


def test_parents_of_different_event_types_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    mom = o.create_event_type('mom')
    dad = o.create_event_type('dad')
    child = o.create_event_type('child')

    mom.create_property('a', 'a').unique()
    dad.create_property('a', 'a').unique()
    child.create_property('a', 'a').set_multi_valued(False)

    mom_of_child = child.make_children('of', mom.is_parent('of', child))
    dad_of_child = child.make_children('of', dad.is_parent('of', child))

    # Comparing two different parents
    # makes no sense and throws an exception.
    assert_incomparable(mom_of_child, dad_of_child)


def test_children_of_different_event_types_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    brother = o.create_event_type('brother')
    sister = o.create_event_type('sister')

    parent.create_property('a', 'a').unique()
    brother.create_property('a', 'a').set_multi_valued(False)
    sister.create_property('a', 'a').set_multi_valued(False)

    parent_of_brother = brother.make_children('of', parent.is_parent('of', brother))
    parent_of_sister = sister.make_children('of', parent.is_parent('of', sister))

    # Comparing two different children
    # makes no sense and throws an exception.
    assert_incomparable(parent_of_brother, parent_of_sister)


def test_parent_description_upgrade():
    o = Ontology()
    o.create_object_type("a")
    parent = o.create_event_type('parent')
    child = o.create_event_type('child')

    parent.create_property("a", "a").unique()
    child.create_property("a", "a").set_multi_valued(False)

    child.make_children('of', parent.is_parent('of', child))

    # Create a new version of the child having different
    # parent description.
    child_copy = copy.deepcopy(child).set_version(2)
    child_copy.get_parent().set_parent_description('changed')

    # Now, the changed copy should be a valid upgrade of the
    # original and vice versa.
    assert_valid_upgrade(child, child_copy)


def test_incompatible_parent_description_upgrade():
    o = Ontology()
    o.create_object_type("a")
    parent = o.create_event_type('parent')
    child = o.create_event_type('child')

    parent.create_property("a", "a").unique()
    child.create_property("a", "a").set_multi_valued(False)

    child.make_children('of', parent.is_parent('of', child))

    # We create a copy having a different description, without incrementing the version.
    child_copy = copy.deepcopy(child)
    child_copy.get_parent().set_parent_description('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(child, child_copy)


def test_siblings_description_upgrade():
    o = Ontology()
    o.create_object_type("a")
    parent = o.create_event_type('parent')
    child = o.create_event_type('child')

    parent.create_property("a", "a").unique()
    child.create_property("a", "a").set_multi_valued(False)

    child.make_children('of', parent.is_parent('of', child))

    # Create a new version of the child having different
    # siblings description.
    child_copy = copy.deepcopy(child).set_version(2)
    child_copy.get_parent().set_siblings_description('changed')

    # Now, the changed copy should be a valid upgrade of the
    # original and vice versa.
    assert_valid_upgrade(child, child_copy)


def test_incompatible_siblings_description_upgrade():
    o = Ontology()
    o.create_object_type("a")
    parent = o.create_event_type('parent')
    child = o.create_event_type('child')

    parent.create_property("a", "a").unique()
    child.create_property("a", "a").set_multi_valued(False)

    child.make_children('of', parent.is_parent('of', child))

    # We create a copy having a different description, without incrementing the version.
    child_copy = copy.deepcopy(child)
    child_copy.get_parent().set_siblings_description('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(child, child_copy)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
