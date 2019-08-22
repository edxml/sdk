"""
Test to verify that updates to event type parent definitions
work as expected. Contrary to test_parent_upgrade, these
tests check comparing and updating of parent definitions within
the context of an event type.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_invalid_ontology_upgrade


def test_copies_are_identical():
    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    parent.create_property('a', 'a').unique()
    child = o.create_event_type('child')
    child.create_property('a', 'a').set_multi_valued(False)

    child.make_children('of', parent.is_parent('of', child))

    # Exact copies should be identical.
    assert child == copy.deepcopy(child)


def test_changing_parent_event_type_not_allowed():
    o = Ontology()
    o.create_object_type('a')
    child_of_mom = o.create_event_type('child')
    child_of_mom.create_property('a', 'a').set_multi_valued(False)

    # Create two different parents
    mom = o.create_event_type('mom')
    dad = o.create_event_type('dad')

    mom.create_property('a', 'a').unique()
    dad.create_property('a', 'a').unique()

    child_of_mom.make_children('of', mom.is_parent('of', child_of_mom))

    # Create a new version having dad as parent
    child_of_dad = copy.deepcopy(child_of_mom).set_version(2)
    child_of_dad.make_children('of', dad.is_parent('of', child_of_dad))

    # Comparing two should now fail.
    assert_invalid_ontology_upgrade(child_of_mom, child_of_dad)


def test_changing_property_map_not_allowed():
    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    parent.create_property('a', 'a').unique()
    child_a = o.create_event_type('child')
    child_a.create_property('a', 'a').set_multi_valued(False)
    child_a.create_property('b', 'a').set_multi_valued(False)

    child_a.make_children('of', parent.is_parent('of', child_a)).map('a', 'a')

    child_b = copy.deepcopy(child_a).set_version(2)
    child_b.make_children('of', parent.is_parent('of', child_a)).map('b', 'a')

    # Comparing two should now fail.
    assert_invalid_ontology_upgrade(child_a, child_b)


def test_add_parent():

    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    parent.create_property('a', 'a').unique()
    child_a = o.create_event_type('child')
    child_a.create_property('a', 'a').set_multi_valued(False)

    child_b = copy.deepcopy(child_a).set_version(2)
    child_b.make_children('of', parent.is_parent('of', child_b))

    # Now, child_b should be a valid upgrade of child_a and vice versa.
    assert_valid_upgrade(child_a, child_b)


def test_remove_parent_not_allowed():

    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    parent.create_property('a', 'a').unique()
    child_a = o.create_event_type('child')
    child_a.create_property('a', 'a').set_multi_valued(False)

    child_b = copy.deepcopy(child_a).set_version(2)

    # Make old version child of parent.
    child_a.make_children('of', parent.is_parent('of', child_a))

    # Comparing two should now fail.
    assert_invalid_ontology_upgrade(child_a, child_b)


def test_parent_attribute_upgrade():
    o = Ontology()
    o.create_object_type('a')

    parent = o.create_event_type('parent')
    parent.create_property('a', 'a').unique()
    child_a = o.create_event_type('child')
    child_a.create_property('a', 'a').set_multi_valued(False)
    child_a.create_property('b', 'a').set_multi_valued(False)

    child_a.make_children('of', parent.is_parent('of', child_a)).map('a', 'a')

    child_b = copy.deepcopy(child_a).set_version(2)
    child_b.get_parent().set_parent_description('changed')

    # Now, child_b should be a valid upgrade of child_a and vice versa.
    assert_valid_upgrade(child_a, child_b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
