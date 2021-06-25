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
from edxml.error import EDXMLOntologyValidationError

from edxml.ontology import EventProperty
from conftest import create_transcoder

# Below tests check for detection of typos in the RecordTranscoder class attributes. For example, when
# the TYPE_PROPERTY_DESCRIPTIONS attribute contains an entry for an event type named 'a' while
# TYPE_PROPERTIES has no corresponding entry for that event type the class attributes are
# mutually inconsistent, typically due to a typo in TYPE_PROPERTY_DESCRIPTIONS.


def test_spurious_type_description_exception(transcoder):
    type(transcoder).TYPE_DESCRIPTIONS = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_display_name_exception(transcoder):
    type(transcoder).TYPE_DISPLAY_NAMES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_multi_valued_properties_exception(transcoder):
    type(transcoder).TYPE_MULTI_VALUED_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_optional_properties_exception(transcoder):
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_mandatory_properties_exception(transcoder):
    type(transcoder).TYPE_MANDATORY_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_auto_normalize_properties_exception(transcoder):
    type(transcoder).TYPE_AUTO_REPAIR_NORMALIZE = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_auto_drop_properties_exception(transcoder):
    type(transcoder).TYPE_AUTO_REPAIR_DROP = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_summary_exception(transcoder):
    type(transcoder).TYPE_SUMMARIES = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_story_exception(transcoder):
    type(transcoder).TYPE_STORIES = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_timespan_exception(transcoder):
    type(transcoder).TYPE_TIMESPANS = {'spurious': [None, None]}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_version_property_exception(transcoder):
    type(transcoder).TYPE_VERSIONS = {'spurious': None}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_media_type_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_MEDIA_TYPES = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_display_name_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_DISPLAY_NAMES = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_description_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_DESCRIPTIONS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_encoding_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_ENCODINGS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_parent_exception(transcoder):
    type(transcoder).PARENT_MAPPINGS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_universals_name_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_NAMES = {'spurious': {'property-a': 'property-a'}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_universals_description_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_DESCRIPTIONS = {'spurious': {'property-a': 'property-a'}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_type_universals_container_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_CONTAINERS = {'spurious': {'property-a': 'property-a'}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(transcoder.generate_event_types())


def test_spurious_property_description_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'spurious': 'test'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_similarity_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_SIMILARITY = {'event-type.a': {'spurious': 'test'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_merge_strategy_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_MERGE_STRATEGIES = {'event-type.a': {'spurious': EventProperty.MERGE_ADD}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_unique_property_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_HASHED_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_multi_valued_property_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_MULTI_VALUED_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_optional_property_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_post_processor_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_POST_PROCESSORS = {'event-type.a': {'spurious': lambda x: [x]}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_concept_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_concept_cnp_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS_CNP = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_concept_attribute_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_universals_name_source_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_NAMES = {'event-type.a': {'property-a': 'spurious'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_universals_name_target_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_NAMES = {'event-type.a': {'spurious': 'property-a'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_universals_description_source_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_DESCRIPTIONS = {'event-type.a': {'property-a': 'spurious'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_universals_description_target_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_DESCRIPTIONS = {'event-type.a': {'spurious': 'property-a'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_universals_container_source_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_CONTAINERS = {'event-type.a': {'property-a': 'spurious'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_universals_container_target_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIVERSALS_CONTAINERS = {'event-type.a': {'spurious': 'property-a'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_property_concept_attribute_wrong_concept_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {
        'event-type.a': {'property-a': {'concept-b': ['object-type.string:attr']}}
    }
    with pytest.raises(ValueError, match='concept is not associated with the property'):
        dict(transcoder.generate_event_types())


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a', 'event-type.b'))])
def test_spurious_child_type_exception(transcoder):
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(transcoder).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(transcoder).PARENTS_CHILDREN = [['spurious-parent', 'of', 'event-type.a']]
    with pytest.raises(ValueError):
        dict(transcoder.generate_event_types())


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a', 'event-type.b'))])
def test_spurious_sibling_type_exception(transcoder):
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(transcoder).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(transcoder).CHILDREN_SIBLINGS = [['spurious-sibling', 'of', 'event-type.a']]
    with pytest.raises(ValueError):
        dict(transcoder.generate_event_types())

# Below we test a variety of other errors in class attributes.


def test_type_without_properties_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {}
    with pytest.raises(ValueError, match='no properties for event type'):
        dict(transcoder.generate_event_types())


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a', 'event-type.b'))])
def test_parent_child_mapping_no_list_exception(transcoder):
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(transcoder).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(transcoder).PARENTS_CHILDREN = [{}]
    with pytest.raises(ValueError, match='not a list'):
        dict(transcoder.generate_event_types())


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a', 'event-type.b'))])
def test_parent_child_mapping_incorrect_length_exception(transcoder):
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(transcoder).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(transcoder).PARENTS_CHILDREN = [[]]
    with pytest.raises(ValueError, match='incorrect number of items'):
        dict(transcoder.generate_event_types())


@pytest.mark.parametrize("transcoder", [(create_transcoder('event-type.a', 'event-type.b'))])
def test_parent_children_siblings_inconsistency_exception(transcoder):
    type(transcoder).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(transcoder).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(transcoder).PARENTS_CHILDREN = [['event-type.a', 'of', 'event-type.b']]
    type(transcoder).CHILDREN_SIBLINGS = [['event-type.b', 'in', 'event-type.b']]
    with pytest.raises(ValueError, match='that event type has no children'):
        dict(transcoder.generate_event_types())


def test_concept_attribute_no_list_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': 'foo'}}}
    with pytest.raises(ValueError, match='not a list'):
        dict(transcoder.generate_event_types())


def test_invalid_concept_attribute_name_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': ['attr']}}}
    with pytest.raises(ValueError, match='does not contain a colon'):
        dict(transcoder.generate_event_types())

    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': []}}}
    with pytest.raises(ValueError, match='not a list of length 1, 2 or 3'):
        dict(transcoder.generate_event_types())


def test_wrong_concept_attribute_name_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': ['foo:attr']}}}
    with pytest.raises(EDXMLOntologyValidationError, match="must begin with 'object-type.string:'"):
        dict(transcoder.generate_event_types())


def test_event_type_version_property_is_not_string(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'version': 'object-type.sequence'}}
    type(transcoder).TYPE_VERSIONS = {'event-type.a': ['version']}
    with pytest.raises(ValueError, match="not a string"):
        dict(transcoder.generate_event_types())
