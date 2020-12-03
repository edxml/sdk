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

from edxml.ontology import Ontology
from tests.assertions import assert_valid_ontology_upgrade, assert_invalid_ontology_upgrade


def create_test_ontology():
    o = Ontology()
    o.create_object_type("a")
    o.create_concept("a")
    o.create_event_source("/a/")

    event_type = o.create_event_type("a")
    event_type.create_property("a", "a")

    return o


def test_copies_are_identical():
    o = create_test_ontology()

    # Exact copies should be identical.
    assert o == copy.deepcopy(o)


def test_concept_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_concept("a").set_version(2).set_description("changed")

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_ontology_upgrade(a, b)


def test_incompatible_concept_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_concept("a").set_description("changed")

    # We did not increment the version on the changed
    # copy, so the two instances are incompatible and cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_source_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_event_source("/a/").set_version(2).set_description("changed")

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_ontology_upgrade(a, b)


def test_incompatible_source_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_event_source("/a/").set_description("changed")

    # We did not increment the version on the changed
    # copy, so the two instances are incompatible and cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_object_type_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_object_type("a").set_version(2).set_description("changed")

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_ontology_upgrade(a, b)


def test_incompatible_object_type_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_object_type("a").set_description("changed")

    # We did not increment the version on the changed
    # copy, so the two instances are incompatible and cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_event_type_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_event_type("a").set_version(2).set_description("changed")

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_ontology_upgrade(a, b)


def test_incompatible_event_type_upgrade():

    a = create_test_ontology()
    b = copy.deepcopy(a)
    b.get_event_type("a").set_description("changed")

    # We did not increment the version on the changed
    # copy, so the two instances are incompatible and cannot be compared.
    assert_invalid_ontology_upgrade(a, b)


def test_add_concept():
    a = create_test_ontology()

    b = copy.deepcopy(a)
    b.create_concept("b")

    # Now b has a concept that a does not have and the two
    # should no longer be equal. Weather b is a valid upgrade
    # of a or the other way around is arbitrary, because
    # upgrades are valid both ways.
    assert a != b
    assert b != a

    # Test that we can merge the ontologies.
    a.update(b)

    # Now the two should be equal.
    assert a == b


def test_add_object_type():
    a = create_test_ontology()

    b = copy.deepcopy(a)
    b.create_object_type("b")

    # Now b has an object type that a does not have and the two
    # should no longer be equal. Weather b is a valid upgrade
    # of a or the other way around is arbitrary, because
    # upgrades are valid both ways.
    assert a != b
    assert b != a

    # Test that we can merge the ontologies.
    a.update(b)

    # Now the two should be equal.
    assert a == b


def test_add_event_source():
    a = create_test_ontology()

    b = copy.deepcopy(a)
    b.create_event_source("/b/")

    # Now b has an event source that a does not have and the two
    # should no longer be equal. Weather b is a valid upgrade
    # of a or the other way around is arbitrary, because
    # upgrades are valid both ways.
    assert a != b
    assert b != a

    # Test that we can merge the ontologies.
    a.update(b)

    # Now the two should be equal.
    assert a == b


def test_add_event_type():
    a = create_test_ontology()

    b = copy.deepcopy(a)
    b.create_event_type("b")

    # Now b has an event type that a does not have and the two
    # should no longer be equal. Weather b is a valid upgrade
    # of a or the other way around is arbitrary, because
    # upgrades are valid both ways.
    assert a != b
    assert b != a

    # Test that we can merge the ontologies.
    a.update(b)

    # Now the two should be equal.
    assert a == b


def test_mixed_upgrade_downgrade():
    a = Ontology()
    a.create_concept("a")
    a.create_concept("b").set_version(2).set_description("changed")

    b = Ontology()
    b.create_concept("a").set_version(2).set_description("changed")
    b.create_concept("b")

    # Now upgrading ontology a to b results in one concept upgrade and one
    # concept downgrade. Since ontology element downgrades are ignored, the
    # mixed upgrade / downgrade must be interpreted as a valid ontology
    # upgrade in both directions.
    assert a > b
    assert b > a

    # Test that we can merge the ontologies both ways.
    a_copy = copy.deepcopy(a)
    b_copy = copy.deepcopy(b)
    assert a_copy.update(b) == b_copy.update(a)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
