"""
Test to verify that updates to event type property definitions
work as expected. Contrary to test_property_upgrade, these
tests check updating of property definitions within the context
of an event type.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable


def test_copies_are_identical():

    o = Ontology()
    o.create_object_type("a")
    a = o.create_event_type("a")
    a.create_property("a", "a")

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_property_order_is_insignificant():

    o1 = Ontology()
    o1.create_object_type("a")
    o2 = copy.deepcopy(o1)

    a = o1.create_event_type("a")
    b = o2.create_event_type("a")

    a.create_property("a", "a")
    a.create_property("b", "a")

    b.create_property("b", "a")
    b.create_property("a", "a")

    # Both event types must be identical, even though
    # the properties are created in different order.
    a == b


def test_removing_property_fails():

    o1 = Ontology()
    o1.create_object_type("a")
    a = o1.create_event_type("a")
    a.create_property("a", "a")
    a.create_property("b", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a").remove_property("a")

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_incomparable(a, b)


def test_adding_property_fails():

    o1 = Ontology()
    o1.create_object_type("a")
    a = o1.create_event_type("a")
    a.create_property("a", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a")
    b.create_property("b", "a")

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_incomparable(a, b)


def test_property_attribute_upgrade():

    o1 = Ontology()
    o1.create_object_type("a")
    a = o1.create_event_type("a")
    a.create_property("a", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a").set_version(2).set_description("changed")

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
