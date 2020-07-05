import pytest

from edxml.ontology import EventProperty
from conftest import create_transcoder

# Below tests check for detection of typos in the Transcoder class attributes. For example, when
# the TYPE_PROPERTY_DESCRIPTIONS attribute contains an entry for an event type named 'a' while
# TYPE_PROPERTIES has no corresponding entry for that event type the class attributes are
# mutually inconsistent, typically due to a typo in TYPE_PROPERTY_DESCRIPTIONS.


def test_spurious_type_description_exception(transcoder):
    type(transcoder).TYPE_DESCRIPTIONS = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_display_name_exception(transcoder):
    type(transcoder).TYPE_DISPLAY_NAMES = {'spurious': []}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_multi_valued_properties_exception(transcoder):
    type(transcoder).TYPE_MULTI_VALUED_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_optional_properties_exception(transcoder):
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_mandatory_properties_exception(transcoder):
    type(transcoder).TYPE_MANDATORY_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_summary_exception(transcoder):
    type(transcoder).TYPE_SUMMARIES = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_story_exception(transcoder):
    type(transcoder).TYPE_STORIES = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_timespan_exception(transcoder):
    type(transcoder).TYPE_TIMESPANS = {'spurious': [None, None]}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENTS = {'spurious': []}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_media_type_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_MEDIA_TYPES = {'spurious': {}}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_display_name_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_DISPLAY_NAMES = {'spurious': {}}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_description_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_DESCRIPTIONS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_attachment_encoding_exception(transcoder):
    type(transcoder).TYPE_ATTACHMENT_ENCODINGS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_type_parent_exception(transcoder):
    type(transcoder).PARENT_MAPPINGS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in TYPE_MAP'):
        dict(transcoder.generate_event_types())


def test_spurious_property_description_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'spurious': 'test'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_similarity_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_SIMILARITY = {'event-type.a': {'spurious': 'test'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_merge_strategy_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_MERGE_STRATEGIES = {'event-type.a': {'spurious': EventProperty.MERGE_ADD}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_unique_property_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_UNIQUE_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_multi_valued_property_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_MULTI_VALUED_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_optional_property_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_post_processor_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_POST_PROCESSORS = {'event-type.a': {'spurious': lambda x: x}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_concept_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(transcoder.generate_event_types())


def test_spurious_property_concept_cnp_exception(transcoder):
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(transcoder).TYPE_PROPERTY_CONCEPTS_CNP = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
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
    type(transcoder).TYPE_MAP = {'selector': 'event-type.a'}
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
