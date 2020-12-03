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
Test to verify that updates to event type property definitions
work as expected. Contrary to test_property_upgrade, these
tests check updating of property definitions within the context
of an event type.
"""

import copy
import pytest

from edxml.ontology import Ontology, DataType
from tests.assertions import assert_valid_upgrade, assert_invalid_ontology_upgrade


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
    assert a == b


def test_removing_property_fails():

    o1 = Ontology()
    o1.create_object_type("a")
    a = o1.create_event_type("a")
    a.create_property("a", "a")
    a.create_property("b", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a").set_version(2).remove_property("a")

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_add_property():

    o1 = Ontology()
    o1.create_object_type("a")
    a = o1.create_event_type("a")
    a.create_property("a", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a").set_version(2)
    b.create_property("b", "a").make_optional()

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_adding_mandatory_property_fails():

    o1 = Ontology()
    o1.create_object_type("a")
    a = o1.create_event_type("a")
    a.create_property("a", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a").set_version(2)
    b.create_property("b", "a").make_mandatory()

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_adding_datetime_to_timeless_event_type_fails():

    o1 = Ontology()
    o1.create_object_type("a")
    o1.create_object_type("b").set_data_type(DataType.datetime())
    a = o1.create_event_type("a")
    a.create_property("a", "a")

    o2 = copy.deepcopy(o1)
    b = o2.get_event_type("a").set_version(2)
    b.create_property("b", "b")

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


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
