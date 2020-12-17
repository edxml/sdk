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

import pytest

from edxml.ontology import EventProperty
from conftest import create_transcoder


def test_event_type(transcoder):
    type(transcoder).VERSION = 2
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert list(event_types.keys()) == ['event-type.a']
    assert event_types['event-type.a'].get_version() == 2


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_descriptions(transcoder):
    type(transcoder).TYPE_DESCRIPTIONS = {'event-type.a': 'test description'}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_description() == 'test description'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_display_names(transcoder):
    type(transcoder).TYPE_DISPLAY_NAMES = {'event-type.a': ['singular test display name', 'plural test display name']}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_display_name_singular() == 'singular test display name'
    assert event_types['event-type.a'].get_display_name_plural() == 'plural test display name'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_story_template(transcoder):
    type(transcoder).TYPE_STORIES = {'event-type.a': 'test story'}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_story_template() == 'test story'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_summary_template(transcoder):
    type(transcoder).TYPE_SUMMARIES = {'event-type.a': 'test summary'}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_summary_template() == 'test summary'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_timespan_open(transcoder):
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'timespan-start': 'datetime'}}
    type(transcoder).TYPE_TIMESPANS = {'event-type.a': ['timespan-start', None]}

    transcoder._ontology.create_object_type('datetime', data_type='datetime')
    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_timespan_property_names() == ('timespan-start', None)


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_timespan_closed(transcoder):
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'timespan-start': 'datetime', 'timespan-end': 'datetime'}}
    type(transcoder).TYPE_TIMESPANS = {'event-type.a': ['timespan-start', 'timespan-end']}

    transcoder._ontology.create_object_type('datetime', data_type='datetime')
    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_timespan_property_names() == ('timespan-start', 'timespan-end')


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_attachments(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert list(event_types['event-type.a'].get_attachments().keys()) == ['test-attachment']


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_attachment_description(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(transcoder).TYPE_ATTACHMENT_DESCRIPTIONS = {'event-type.a': {'test-attachment': 'test-description'}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment').get_description() == 'test-description'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_attachment_display_name(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(transcoder).TYPE_ATTACHMENT_DISPLAY_NAMES = {'event-type.a': {'test-attachment': ['test-display-name']}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment')\
        .get_display_name_singular() == 'test-display-name'
    assert event_types['event-type.a'].get_attachment('test-attachment')\
        .get_display_name_plural() == 'test-display-names'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_attachment_encoding(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(transcoder).TYPE_ATTACHMENT_ENCODINGS = {'event-type.a': {'test-attachment': 'base64'}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment').get_encoding() == 'base64'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a'))])
def test_event_type_attachment_media_type(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(transcoder).TYPE_ATTACHMENT_MEDIA_TYPES = {'event-type.a': {'test-attachment': 'application/test'}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment').get_media_type() == 'application/test'


def test_properties(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }
    type(transcoder).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'property-a': 'test description'}}
    type(transcoder).TYPE_PROPERTY_SIMILARITY = {'event-type.a': {'property-a': 'test similarity'}}
    type(transcoder).TYPE_PROPERTY_MERGE_STRATEGIES = {'event-type.a': {'property-a': EventProperty.MERGE_MATCH}}
    type(transcoder).TYPE_HASHED_PROPERTIES = {'event-type.a': ['property-a']}
    type(transcoder).TYPE_MULTI_VALUED_PROPERTIES = {'event-type.a': ['property-a']}
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['property-b']}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    for event_type in event_types.values():
        assert list(event_type.get_properties().keys()) == ['property-a', 'property-b']
        assert event_type.get_properties()['property-a'].get_description() == 'test description'
        assert event_type.get_properties()['property-a'].get_similar_hint() == 'test similarity'
        assert event_type.get_properties()['property-a'].get_merge_strategy() == EventProperty.MERGE_MATCH
        assert event_type.get_properties()['property-a'].is_hashed()
        assert event_type.get_properties()['property-a'].is_multi_valued()
        assert event_type.get_properties()['property-a'].is_mandatory()
        assert event_type.get_properties()['property-b'].is_hashed() is False
        assert event_type.get_properties()['property-b'].is_single_valued()
        assert event_type.get_properties()['property-b'].is_optional()


def test_optional_mandatory_properties(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }

    # Make one property optional.
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['property-a']}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    for event_type in event_types.values():
        assert event_type.get_properties()['property-a'].is_optional()
        assert event_type.get_properties()['property-b'].is_mandatory()


def test_optional_mandatory_properties_b(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }

    # Make all properties optional, except for one.
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': True}
    type(transcoder).TYPE_MANDATORY_PROPERTIES = {'event-type.a': ['property-b']}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    for event_type in event_types.values():
        assert event_type.get_properties()['property-a'].is_optional()
        assert event_type.get_properties()['property-b'].is_mandatory()


def test_universals_relations(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }
    type(transcoder).TYPE_UNIVERSALS_NAMES = {'event-type.a': {'property-a': 'property-b'}}
    type(transcoder).TYPE_UNIVERSALS_DESCRIPTIONS = {'event-type.a': {'property-a': 'property-b'}}
    type(transcoder).TYPE_UNIVERSALS_CONTAINERS = {'event-type.a': {'property-a': 'property-b'}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    for event_type in event_types.values():
        assert event_type.get_properties()['property-b'].is_single_valued()
        for relation_type in ['name', 'description', 'container']:
            assert event_type.get_property_relations(relation_type) != {}
            assert list(event_type.get_property_relations(relation_type).values())[0].get_type() == relation_type
            assert list(event_type.get_property_relations(relation_type).values())[0].get_source() == 'property-b'
            assert list(event_type.get_property_relations(relation_type).values())[0].get_target() == 'property-a'


def test_concept_associations(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'property-a': 'test description'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 1}}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS_CNP = {'event-type.a': {'property-a': {'concept-a': 0}}}
    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {
        'event-type.a': {'property-a': {'concept-a': ['object-type.string:attr', 'attr-s', 'attr-p']}}
    }

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    for event_type in event_types.values():
        assert list(event_type['property-a'].get_concept_associations().keys()) == ['concept-a']

        association = event_type['property-a'].get_concept_associations()['concept-a']

        assert association.get_confidence() == 1
        assert association.get_concept_naming_priority() == 0
        assert association.get_attribute_name_extension() == 'attr'
        assert association.get_attribute_display_name_singular() == 'attr-s'
        assert association.get_attribute_display_name_plural() == 'attr-p'


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a', 'event-type.b'))])
def test_event_type_parents(transcoder):
    type(transcoder).TYPE_HASHED_PROPERTIES = {'event-type.a': ['property-a']}
    type(transcoder).PARENTS_CHILDREN = [['event-type.a', 'test parent of', 'event-type.b']]
    type(transcoder).CHILDREN_SIBLINGS = [['event-type.b', 'test sibling of', 'event-type.a']]
    type(transcoder).PARENT_MAPPINGS = {'event-type.b': {'property-a': 'property-a'}}

    event_types = dict(transcoder.generate_event_types())
    transcoder._ontology.validate()

    assert event_types['event-type.b'].get_parent().get_event_type_name() == 'event-type.a'
    assert event_types['event-type.b'].get_parent().get_parent_description() == 'test parent of'
    assert event_types['event-type.b'].get_parent().get_siblings_description() == 'test sibling of'
    assert event_types['event-type.b'].get_parent().get_property_map() == {'property-a': 'property-a'}
