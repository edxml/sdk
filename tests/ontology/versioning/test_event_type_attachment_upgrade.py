"""
Test to verify that updates to event type attachment definitions
work as expected. Contrary to test_attachment_upgrade, these
tests check comparing and updating of attachment definitions within
the context of an event type.
"""

import copy
import pytest

from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_invalid_ontology_upgrade


def test_copies_are_identical():
    o = Ontology()

    type = o.create_event_type('a')
    type.create_attachment('a')

    # Exact copies should be identical.
    assert type == copy.deepcopy(type)


def test_changing_media_type_not_allowed():
    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_version(2)

    # Create attachment with different media types
    a.create_attachment('a').set_media_type('some/type')
    b.create_attachment('a').set_media_type('different/type')

    # Comparing the two should now fail.
    assert_invalid_ontology_upgrade(a, b)


def test_changing_encoding_not_allowed():
    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_version(2)

    # Create attachment with different content encodings
    a.create_attachment('a').set_encoding_unicode()
    b.create_attachment('a').set_encoding_base64()

    # Comparing the two should now fail.
    assert_invalid_ontology_upgrade(a, b)


def test_remove_attachment_not_allowed():
    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_version(2)

    # Create attachment on type a only.
    a.create_attachment('a').set_encoding_unicode()

    # Comparing the two should now fail.
    assert_invalid_ontology_upgrade(a, b)


def test_description_upgrade():
    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_version(2)

    # Create attachments with different descriptions
    a.create_attachment('a').set_description('something')
    b.create_attachment('a').set_description('different')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_display_name_upgrade():
    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_version(2)

    # Create attachments with different display names
    a.create_attachment('a').set_display_name('something')
    b.create_attachment('a').set_display_name('different')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_add_attachment():
    o = Ontology()
    a = o.create_event_type('a')
    b = copy.deepcopy(a).set_version(2)

    # Create attachment on b
    b.create_attachment('a')

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
