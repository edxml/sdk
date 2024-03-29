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

from edxml.ontology import Ontology, DataType
from tests.assertions import assert_valid_upgrade, assert_incomparable, assert_invalid_ontology_upgrade


def test_different_event_types_cannot_be_compared():
    o = Ontology()
    a = o.create_event_type('a')
    b = o.create_event_type('b')

    # Comparing two event types with different names
    # makes no sense and throws an exception.
    assert_incomparable(a, b)


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

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


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

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_set_timespan_not_allowed():

    o = Ontology()
    o.create_object_type('datetime')
    a = o.create_event_type('a')
    a.create_property('start', 'datetime')
    a.create_property('end', 'datetime')

    # Create a copy that sets the timespan start property.
    b = copy.deepcopy(a).set_timespan_property_name_start('start').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)

    # Create a copy that sets the timespan end property.
    b = copy.deepcopy(a).set_timespan_property_name_end('end').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_change_timespan_not_allowed():

    o = Ontology()
    o.create_object_type('datetime')
    a = o.create_event_type('a')
    a.create_property('start', 'datetime')
    a.create_property('end', 'datetime')
    a.set_timespan_property_name_start('start')
    a.set_timespan_property_name_end('end')

    # Create a copy that changes the timespan start property.
    b = copy.deepcopy(a).set_timespan_property_name_start('end').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)

    # Create a copy that changes the timespan end property.
    b = copy.deepcopy(a).set_timespan_property_name_end('start').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_set_event_version_not_allowed():

    o = Ontology()
    o.create_object_type('sequence', data_type=DataType.FAMILY_SEQUENCE)
    a = o.create_event_type('a')
    a.create_property('version', 'sequence').merge_max()

    # Create a copy that sets the event version property.
    b = copy.deepcopy(a).set_version_property_name('version').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_change_event_version_not_allowed():

    o = Ontology()
    o.create_object_type('sequence', data_type=DataType.FAMILY_SEQUENCE)
    a = o.create_event_type('a')
    a.create_property('version-a', 'sequence').merge_max()
    a.create_property('version-b', 'sequence').merge_max()
    a.set_version_property_name('version-a')

    # Create a copy that sets a different version property.
    b = copy.deepcopy(a).set_version_property_name('version-b').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_set_event_sequence_not_allowed():

    o = Ontology()
    o.create_object_type('sequence', data_type=DataType.FAMILY_SEQUENCE)
    a = o.create_event_type('a')
    a.create_property('sequence', 'sequence')

    # Create a copy that sets the event sequence property.
    b = copy.deepcopy(a).set_sequence_property_name('sequence').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_change_event_sequence_not_allowed():

    o = Ontology()
    o.create_object_type('sequence', data_type=DataType.FAMILY_SEQUENCE)
    a = o.create_event_type('a')
    a.create_property('sequence-a', 'sequence')
    a.create_property('sequence-b', 'sequence')
    a.set_sequence_property_name('sequence-a')

    # Create a copy that sets a different event sequence property.
    b = copy.deepcopy(a).set_sequence_property_name('sequence-b').set_version(2)

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


def test_timeless_to_timeful_not_allowed():

    o = Ontology()
    o.create_object_type('string')
    o.create_object_type('datetime', data_type=DataType.FAMILY_DATETIME)
    a = o.create_event_type('a')
    a.create_property('string', object_type_name='string')

    # Create a copy adding a datetime property.
    b = copy.deepcopy(a).set_version(2)
    b.create_property('datetime', object_type_name='datetime').make_optional()

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


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

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


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

    # The versions are now incompatible.
    assert_invalid_ontology_upgrade(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
