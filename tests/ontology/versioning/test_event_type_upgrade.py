import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable


def test_different_event_types_cannot_be_compared():
    o = Ontology()
    a = o.create_event_type('a')
    b = o.create_event_type('b')

    # Comparing two event types with different names
    # makes no sense and throws an exception.
    with pytest.raises(Exception):
        a > b


def test_copies_are_identical():
    o = Ontology()
    a = o.create_event_type('a')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_description_upgrade():

    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_description('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_description_upgrade():

    o = Ontology()
    a = o.create_event_type('a')

    # We change the description without incrementing the version.
    b = copy.deepcopy(a).set_description('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_display_name_upgrade():

    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_display_name('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_display_name_upgrade():

    o = Ontology()
    a = o.create_event_type('a')

    # We change the display name without incrementing the version.
    b = copy.deepcopy(a).set_display_name('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_class_order_is_insignificant():

    o = Ontology()
    a = o.create_event_type('a').set_classes(['a', 'b'])
    b = copy.deepcopy(a).set_classes(['b', 'a'])

    # Now, a and b should be identical.
    assert a == b


def test_add_class():

    o = Ontology()
    a = o.create_event_type('a').set_classes(['a', 'b'])
    b = copy.deepcopy(a).add_class('b').add_class('c').set_version(2)
    c = copy.deepcopy(a).set_classes(['a', 'b', 'c']).set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)

    # And the two event type classes should be combined.
    assert b == c


def test_remove_class_not_allowed():

    o = Ontology()
    a = o.create_event_type('a').set_classes(['a', 'b'])

    # Create a copy that is missing one class.
    b = copy.deepcopy(a).set_classes(['a']).set_version(2)

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)

    # Create a copy that is missing one class while adding another.
    b = copy.deepcopy(a).set_classes(['a', 'c']).set_version(2)

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_summary_upgrade():

    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_summary_template('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_summary_upgrade():

    o = Ontology()
    a = o.create_event_type('a')

    # We change the summary template without incrementing the version.
    b = copy.deepcopy(a).set_summary_template('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_story_upgrade():

    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_story_template('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_story_upgrade():

    o = Ontology()
    a = o.create_event_type('a')

    # We change the story template without incrementing the version.
    b = copy.deepcopy(a).set_story_template('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
