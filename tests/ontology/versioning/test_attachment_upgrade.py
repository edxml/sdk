"""
Test to verify that updates to event type attachment definitions
work as expected. Contrary to test_event_type_attachment_upgrade, these
tests check comparing and updating of isolated attachment definitions.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable, assert_invalid_ontology_upgrade


def test_different_attachments_cannot_be_compared():
    o = Ontology()

    e = o.create_event_type('a')
    a = e.create_attachment('a')
    b = e.create_attachment('b')

    # Comparing two attachments with different names
    # makes no sense and throws an exception.
    assert_incomparable(a, b)


def test_attachments_of_different_event_types_cannot_be_compared():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a').create_attachment('a')
    b = o.create_event_type('b').create_attachment('a')

    # Comparing two attachments with different names
    # makes no sense and throws an exception.
    assert_invalid_ontology_upgrade(a, b)


def test_copies_are_identical():
    o = Ontology()

    e = o.create_event_type('a')
    a = e.create_attachment('a')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_description_upgrade():
    o = Ontology()

    a = o.create_event_type('a')
    a.create_attachment('a')
    b = copy.deepcopy(a).set_version(2)
    b.get_attachment('a').set_description('changed')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_description_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_attachment('a')

    # We change the description without incrementing the version.
    b = copy.deepcopy(a)
    b.get_attachment('a').set_description('changed')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_display_name_upgrade():
    o = Ontology()

    a = o.create_event_type('a')
    a.create_attachment('a')
    b = copy.deepcopy(a).set_version(2)
    b.get_attachment('a').set_display_name('changed')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_display_name_upgrade():
    o = Ontology()
    o.create_object_type('a')

    a = o.create_event_type('a')
    a.create_attachment('a')

    # We change the display name without incrementing the version.
    b = copy.deepcopy(a)
    b.get_attachment('a').set_display_name('changed')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_change_media_type_not_allowed():
    o = Ontology()

    a = o.create_event_type('a')
    a.create_attachment('a').set_media_type('some/type')

    # We make a newer attachment in which the media type has changed.
    b = copy.deepcopy(a).set_version(2)
    b.get_attachment('a').set_media_type('other/type')

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_change_encoding_not_allowed():
    o = Ontology()

    a = o.create_event_type('a')
    a.create_attachment('a').set_encoding_unicode()

    # We make a newer attachment in which the content encoding has changed.
    b = copy.deepcopy(a).set_version(2)
    b.get_attachment('a').set_encoding_base64()

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
