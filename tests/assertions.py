import copy
import pytest

from edxml.EDXMLBase import EDXMLValidationError


def assert_valid_upgrade(old, new):
    """

    Asserts that two given ontology elements are valid
    upgrades of one another.

    Args:
        old (edxml.Ontology.OntologyElement):
        new (edxml.Ontology.OntologyElement):

    """
    assert new > old
    assert old < new

    # Updating the new version with the old version
    # should not change the new version.
    new_copy = copy.deepcopy(new)
    new.update(old)
    assert new == new_copy

    # Updating the old version with the new version
    # should make both identical.
    old.update(new)
    assert old == new


def assert_incomparable(a, b):
    # An attempt to upgrade should now fail.
    with pytest.raises(EDXMLValidationError):
        a == b
