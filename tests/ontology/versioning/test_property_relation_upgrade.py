"""
Test to verify that updates to property relation definitions
work as expected. Contrary to test_event_type_property_relation_upgrade, these
tests check comparing and updating of isolated relation definitions.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_invalid_ontology_upgrade


def test_copies_are_identical():
    o = Ontology()
    o.create_object_type('a')

    e = o.create_event_type('a')
    e.create_property('a', 'a')
    e.create_property('b', 'a')
    a = e['a'].relate_to('related to', 'b')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_different_relations_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    e = o.create_event_type('a')
    p1 = e.create_property('p1', 'a')
    e.create_property('p2', 'a')
    e.create_property('p3', 'a')

    a = p1.relate_to('related to', 'p2')
    b = p1.relate_to('related to', 'p3')

    # Comparing two relations between different properties
    # makes no sense and throws an exception.
    with pytest.raises(Exception):
        a > b


def test_relations_between_properties_of_different_event_types_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a')
    e1.create_property('b', 'a')
    a = e1['a'].relate_to('related to', 'b')

    e2 = o.create_event_type('b')
    e2.create_property('a', 'a')
    e2.create_property('b', 'a')
    b = e2['a'].relate_to('related to', 'b')

    # Comparing two relations from different event types
    # makes no sense and throws an exception.
    assert_invalid_ontology_upgrade(a, b)


def test_change_source_property_not_allowed():

    o = Ontology()
    o.create_object_type('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a')
    e1.create_property('b', 'a')
    e1.create_property('c', 'a')

    e2 = copy.deepcopy(e1).set_version(2)

    a = e1['a'].relate_to('related to', 'c')
    b = e2['b'].relate_to('related to', 'c')

    # An attempt to upgrade to a version having a different
    # source property must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_change_target_property_not_allowed():

    o = Ontology()
    o.create_object_type('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a')
    e1.create_property('b', 'a')
    e1.create_property('c', 'a')

    e2 = copy.deepcopy(e1).set_version(2)

    a = e1['a'].relate_to('related to', 'b')
    b = e2['a'].relate_to('related to', 'c')

    # An attempt to upgrade to a version having a different
    # target property must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_change_directedness_not_allowed():
    o = Ontology()
    o.create_object_type('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a')
    e1.create_property('b', 'a')

    e2 = copy.deepcopy(e1).set_version(2)

    a = e1['a'].relate_to('related to', 'b').make_undirected()
    b = e2['a'].relate_to('related to', 'b').make_directed()

    # An attempt to upgrade to a version having a different
    # relation directedness must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_change_relation_type_not_allowed():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    e1 = o.create_event_type('a')
    e1.create_property('a', 'a').identifies('a', 1)
    e1.create_property('b', 'a').identifies('a', 1)

    e2 = copy.deepcopy(e1).set_version(2)

    a = e1['a'].relate_inter('related to', 'b')
    b = e2['a'].relate_intra('related to', 'b')

    # An attempt to upgrade to a version having a different
    # relation type must fail.
    assert_invalid_ontology_upgrade(a, b)


def test_description_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')
    a.create_property('b', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].relate_to('related to', 'b').because('[[a]] is related to [[b]]')
    b['a'].relate_to('related to', 'b').because('[[b]] is related to [[a]]')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_predicate_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')
    a.create_property('b', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].relate_to('associated with', 'b')
    b['a'].relate_to('related to', 'b')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_confidence_upgrade():
    o = Ontology()
    o.create_object_type('a')
    o.create_concept('a')

    a = o.create_event_type('a')
    a.create_property('a', 'a')
    a.create_property('b', 'a')

    b = copy.deepcopy(a).set_version(2)

    a['a'].relate_to('related to', 'b').set_confidence(1)
    b['a'].relate_to('related to', 'b').set_confidence(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
