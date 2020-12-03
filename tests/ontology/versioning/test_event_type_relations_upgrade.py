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
work as expected. Contrary to test_property_relation_upgrade, these
tests check updating of property relations within the context
of an event type.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_invalid_ontology_upgrade


def test_copies_are_identical():

    o = Ontology()
    o.create_object_type("a")
    e = o.create_event_type("a")
    e.create_property("a", "a")
    e.create_property("b", "a")

    e["a"].relate_to('related to', 'b')

    # Exact copies should be identical.
    assert e == copy.deepcopy(e)


def test_relation_order_is_insignificant():

    o1 = Ontology()
    o1.create_object_type("a")
    o2 = copy.deepcopy(o1)

    a = o1.create_event_type("a")
    b = o2.create_event_type("a")

    a.create_property("a", "a")
    a.create_property("b", "a")
    a.create_property("c", "a")

    a["a"].relate_to('related to', 'b')
    a["b"].relate_to('related to', 'c')

    b.create_property("a", "a")
    b.create_property("b", "a")
    b.create_property("c", "a")

    b["b"].relate_to('related to', 'c')
    b["a"].relate_to('related to', 'b')

    # Both event types must be identical, even though
    # the relations are created in different order.
    assert a == b


def test_change_relation_concept_source():

    o1 = Ontology()
    o1.create_object_type("a")
    o1.create_concept("a")
    o1.create_concept("b")
    o2 = copy.deepcopy(o1)

    a = o1.create_event_type("a")
    b = o2.create_event_type("a").set_version(2)

    # The two event type versions will have inter-concept
    # relations that have different source concepts.
    a.create_property("a", "a").identifies('a')
    a.create_property("b", "a").identifies('a')
    a["a"].relate_inter('related to', 'b')

    b.create_property("a", "a").identifies('b')
    b.create_property("b", "a").identifies('a')
    b["a"].relate_inter('related to', 'b')

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_change_relation_concept_target():

    o1 = Ontology()
    o1.create_object_type("a")
    o1.create_concept("a")
    o1.create_concept("b")
    o2 = copy.deepcopy(o1)

    a = o1.create_event_type("a")
    b = o2.create_event_type("a").set_version(2)

    # The two event type versions will have inter-concept
    # relations that have different target concepts.
    a.create_property("a", "a").identifies('a')
    a.create_property("b", "a").identifies('a')
    a["a"].relate_inter('related to', 'b')

    b.create_property("a", "a").identifies('a')
    b.create_property("b", "a").identifies('b')
    b["a"].relate_inter('related to', 'b')

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_add_relation():

    o1 = Ontology()
    o1.create_object_type("a")
    o2 = copy.deepcopy(o1)

    a = o1.create_event_type("a")
    b = o2.create_event_type("a").set_version(2)

    a.create_property("a", "a")
    a.create_property("b", "a")
    a.create_property("c", "a")
    a["a"].relate_to('related to', 'b')

    b.create_property("a", "a")
    b.create_property("b", "a")
    b.create_property("c", "a")

    b["a"].relate_to('related to', 'b')
    b["b"].relate_to('related to', 'c')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_removing_relation_fails():

    o1 = Ontology()
    o1.create_object_type("a")
    o2 = copy.deepcopy(o1)

    a = o1.create_event_type("a")
    b = o2.create_event_type("a").set_version(2)

    a.create_property("a", "a")
    a.create_property("b", "a")
    a.create_property("c", "a")

    a["a"].relate_to('related to', 'b')
    a["b"].relate_to('related to', 'c')

    b.create_property("a", "a")
    b.create_property("b", "a")
    b.create_property("c", "a")

    b["b"].relate_to('related to', 'c')

    # The two versions of the event type are now incompatible and
    # cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_relation_attribute_upgrade():

    o = Ontology()
    o.create_object_type("a")
    a = o.create_event_type("a")
    a.create_property("p1", "a")
    a.create_property("p2", "a")

    a['p1'].relate_to('related to', 'p2').set_description('[[p1]] related to [[p2]]')

    b = copy.deepcopy(a).set_version(2)
    for relation in b.relations:
        relation.set_description('[[p2]] related to [[p1]]')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
