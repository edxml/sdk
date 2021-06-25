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

from edxml.error import EDXMLOntologyValidationError


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


def assert_valid_ontology_upgrade(old, new):
    """

    Asserts that two given ontologies are valid
    upgrades of one another.

    Args:
        old (edxml.Ontology.OntologyElement):
        new (edxml.Ontology.OntologyElement):

    """

    # Ontologies can only be upgrades of one another
    # in both directions, not downgrades.
    assert new > old
    assert old > new

    # Updating the old version with the new version
    # and vice versa should make both identical.
    old.update(new)
    new.update(old)
    assert old == new


def assert_invalid_ontology_upgrade(old, new, match=None):
    with pytest.raises(EDXMLOntologyValidationError, match=match):
        assert new > old


def assert_incomparable(a, b):
    # An attempt to upgrade should now fail.
    with pytest.raises(ValueError):
        assert a == b
