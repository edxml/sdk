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
from edxml.ontology import EventProperty, Ontology, DataType, EventTypeFactory


@pytest.fixture()
def factory():
    class TestFactory(EventTypeFactory):
        """
        This extension of EventTypeFactory allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        EventTypeFactory class would cause side effects because that class is
        shared by all tests.
        """
        pass

    t = TestFactory()
    ontology = Ontology()
    ontology.create_concept('concept-a', 'concept')
    ontology.create_object_type('object-type.string')
    ontology.create_object_type('object-type.integer', data_type=DataType.int().get())
    t.set_ontology(ontology)
    return t


def create_factory(*event_type_names):
    """

    Helper function to generate an event type factory producing
    the specified event types.

    Args:
        *event_type_names (str):

    Returns:
        edxml.ontology.event_type_factory.EventTypeFactory:
    """
    class TestFactory(EventTypeFactory):
        """
        This extension of EventTypeFactory allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        EventTypeFactory class would cause side effects because that class is
        shared by all tests.
        """
        pass

    TestFactory.TYPES = event_type_names
    TestFactory.TYPE_PROPERTIES = {name: {'property-a': 'object-type.string'} for name in event_type_names}
    t = TestFactory()
    ontology = Ontology()
    ontology.create_object_type('object-type.string')
    t.set_ontology(ontology)
    return t


def test_event_type(factory):
    type(factory).VERSION = 2
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert list(event_types.keys()) == ['event-type.a']
    assert event_types['event-type.a'].get_version() == 2


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_descriptions(factory):
    type(factory).TYPE_DESCRIPTIONS = {'event-type.a': 'test description'}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_description() == 'test description'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_display_names(factory):
    type(factory).TYPE_DISPLAY_NAMES = {'event-type.a': ['singular test display name', 'plural test display name']}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_display_name_singular() == 'singular test display name'
    assert event_types['event-type.a'].get_display_name_plural() == 'plural test display name'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_display_name_string(factory):
    type(factory).TYPE_DISPLAY_NAMES = {'event-type.a': 'display name'}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_display_name_singular() == 'display name'
    assert event_types['event-type.a'].get_display_name_plural() == 'display names'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_story_template(factory):
    type(factory).TYPE_STORIES = {'event-type.a': 'test story'}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_story_template() == 'test story'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_summary_template(factory):
    type(factory).TYPE_SUMMARIES = {'event-type.a': 'test summary'}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_summary_template() == 'test summary'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_timespan_open(factory):
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'timespan-start': 'datetime'}}
    type(factory).TYPE_TIME_SPANS = {'event-type.a': ['timespan-start', None]}

    factory._ontology.create_object_type('datetime', data_type='datetime')
    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_timespan_property_names() == ('timespan-start', None)


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_timespan_closed(factory):
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'timespan-start': 'datetime', 'timespan-end': 'datetime'}}
    type(factory).TYPE_TIME_SPANS = {'event-type.a': ['timespan-start', 'timespan-end']}

    factory._ontology.create_object_type('datetime', data_type='datetime')
    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_timespan_property_names() == ('timespan-start', 'timespan-end')


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_attachments(factory):
    type(factory).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert list(event_types['event-type.a'].get_attachments().keys()) == ['test-attachment']


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_attachment_description(factory):
    type(factory).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(factory).TYPE_ATTACHMENT_DESCRIPTIONS = {'event-type.a': {'test-attachment': 'test-description'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment').get_description() == 'test-description'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_attachment_display_name_list(factory):
    type(factory).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(factory).TYPE_ATTACHMENT_DISPLAY_NAMES = {'event-type.a': {'test-attachment': ['test-display-name']}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment')\
        .get_display_name_singular() == 'test-display-name'
    assert event_types['event-type.a'].get_attachment('test-attachment')\
        .get_display_name_plural() == 'test-display-names'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_attachment_display_name_string(factory):
    type(factory).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(factory).TYPE_ATTACHMENT_DISPLAY_NAMES = {'event-type.a': {'test-attachment': 'test-display-name'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment')\
        .get_display_name_singular() == 'test-display-name'
    assert event_types['event-type.a'].get_attachment('test-attachment')\
        .get_display_name_plural() == 'test-display-names'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_attachment_encoding(factory):
    type(factory).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(factory).TYPE_ATTACHMENT_ENCODINGS = {'event-type.a': {'test-attachment': 'base64'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment').get_encoding() == 'base64'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a'))])
def test_event_type_attachment_media_type(factory):
    type(factory).TYPE_ATTACHMENTS = {'event-type.a': ['test-attachment']}
    type(factory).TYPE_ATTACHMENT_MEDIA_TYPES = {'event-type.a': {'test-attachment': 'application/test'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.a'].get_attachment('test-attachment').get_media_type() == 'application/test'


def test_properties(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }
    type(factory).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'property-a': 'test description'}}
    type(factory).TYPE_PROPERTY_SIMILARITY = {'event-type.a': {'property-a': 'test similarity'}}
    type(factory).TYPE_PROPERTY_MERGE_STRATEGIES = {'event-type.a': {'property-a': EventProperty.MERGE_MATCH}}
    type(factory).TYPE_HASHED_PROPERTIES = {'event-type.a': ['property-a']}
    type(factory).TYPE_MULTI_VALUED_PROPERTIES = {'event-type.a': ['property-a']}
    type(factory).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['property-b']}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

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


def test_optional_mandatory_properties(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }

    # Make one property optional.
    type(factory).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['property-a']}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    for event_type in event_types.values():
        assert event_type.get_properties()['property-a'].is_optional()
        assert event_type.get_properties()['property-b'].is_mandatory()


def test_optional_mandatory_properties_b(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }

    # Make all properties optional, except for one.
    type(factory).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': True}
    type(factory).TYPE_MANDATORY_PROPERTIES = {'event-type.a': ['property-b']}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    for event_type in event_types.values():
        assert event_type.get_properties()['property-a'].is_optional()
        assert event_type.get_properties()['property-b'].is_mandatory()


def test_universals_relations(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {
            'property-a': 'object-type.string',
            'property-b': 'object-type.string'
        }
    }
    type(factory).TYPE_UNIVERSALS_NAMES = {'event-type.a': {'property-a': 'property-b'}}
    type(factory).TYPE_UNIVERSALS_DESCRIPTIONS = {'event-type.a': {'property-a': 'property-b'}}
    type(factory).TYPE_UNIVERSALS_CONTAINERS = {'event-type.a': {'property-a': 'property-b'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    for event_type in event_types.values():
        assert event_type.get_properties()['property-b'].is_single_valued()
        for relation_type in ['name', 'description', 'container']:
            assert event_type.get_property_relations(relation_type) != {}
            assert list(event_type.get_property_relations(relation_type).values())[0].get_type() == relation_type
            assert list(event_type.get_property_relations(relation_type).values())[0].get_source() == 'property-b'
            assert list(event_type.get_property_relations(relation_type).values())[0].get_target() == 'property-a'


def test_concept_associations(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'property-a': 'test description'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 1}}}
    type(factory).TYPE_PROPERTY_CONCEPTS_CNP = {'event-type.a': {'property-a': {'concept-a': 0}}}
    type(factory).TYPE_PROPERTY_ATTRIBUTES = {
        'event-type.a': {'property-a': {'concept-a': ['object-type.string:attr', 'attr-s', 'attr-p']}}
    }

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    for event_type in event_types.values():
        assert list(event_type['property-a'].get_concept_associations().keys()) == ['concept-a']

        association = event_type['property-a'].get_concept_associations()['concept-a']

        assert association.get_confidence() == 1
        assert association.get_concept_naming_priority() == 0
        assert association.get_attribute_name_extension() == 'attr'
        assert association.get_attribute_display_name_singular() == 'attr-s'
        assert association.get_attribute_display_name_plural() == 'attr-p'


@pytest.mark.parametrize('factory', [(create_factory('event-type.a', 'event-type.b'))])
def test_event_type_parents(factory):
    type(factory).TYPE_HASHED_PROPERTIES = {'event-type.a': ['property-a']}
    type(factory).PARENTS_CHILDREN = [['event-type.a', 'test parent of', 'event-type.b']]
    type(factory).CHILDREN_SIBLINGS = [['event-type.b', 'test sibling of', 'event-type.a']]
    type(factory).PARENT_MAPPINGS = {'event-type.b': {'property-a': 'property-a'}}

    event_types = dict(factory.generate_event_types())
    factory._ontology.validate()

    assert event_types['event-type.b'].get_parent().get_event_type_name() == 'event-type.a'
    assert event_types['event-type.b'].get_parent().get_parent_description() == 'test parent of'
    assert event_types['event-type.b'].get_parent().get_siblings_description() == 'test sibling of'
    assert event_types['event-type.b'].get_parent().get_property_map() == {'property-a': 'property-a'}


def test_spurious_type_description_exception(factory):
    type(factory).TYPE_DESCRIPTIONS = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_display_name_exception(factory):
    type(factory).TYPE_DISPLAY_NAMES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_multi_valued_properties_exception(factory):
    type(factory).TYPE_MULTI_VALUED_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_optional_properties_exception(factory):
    type(factory).TYPE_OPTIONAL_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_mandatory_properties_exception(factory):
    type(factory).TYPE_MANDATORY_PROPERTIES = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_summary_exception(factory):
    type(factory).TYPE_SUMMARIES = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_story_exception(factory):
    type(factory).TYPE_STORIES = {'spurious': 'test'}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_timespan_exception(factory):
    type(factory).TYPE_TIME_SPANS = {'spurious': [None, None]}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_version_property_exception(factory):
    type(factory).TYPE_VERSIONS = {'spurious': None}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_attachment_exception(factory):
    type(factory).TYPE_ATTACHMENTS = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_attachment_media_type_exception(factory):
    type(factory).TYPE_ATTACHMENT_MEDIA_TYPES = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_attachment_display_name_exception(factory):
    type(factory).TYPE_ATTACHMENT_DISPLAY_NAMES = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_attachment_description_exception(factory):
    type(factory).TYPE_ATTACHMENT_DESCRIPTIONS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_attachment_encoding_exception(factory):
    type(factory).TYPE_ATTACHMENT_ENCODINGS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_parent_exception(factory):
    type(factory).PARENT_MAPPINGS = {'spurious': {}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_universals_name_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_NAMES = {'spurious': {'property-a': 'property-a'}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_universals_description_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_DESCRIPTIONS = {'spurious': {'property-a': 'property-a'}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_type_universals_container_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_CONTAINERS = {'spurious': {'property-a': 'property-a'}}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        dict(factory.generate_event_types())


def test_spurious_property_description_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_DESCRIPTIONS = {'event-type.a': {'spurious': 'test'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_similarity_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_SIMILARITY = {'event-type.a': {'spurious': 'test'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_merge_strategy_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_MERGE_STRATEGIES = {'event-type.a': {'spurious': EventProperty.MERGE_ADD}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_unique_property_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_HASHED_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_multi_valued_property_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_MULTI_VALUED_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_optional_property_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_OPTIONAL_PROPERTIES = {'event-type.a': ['spurious']}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_concept_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_concept_cnp_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(factory).TYPE_PROPERTY_CONCEPTS_CNP = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_concept_attribute_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(factory).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'spurious': {}}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_universals_name_source_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_NAMES = {'event-type.a': {'property-a': 'spurious'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_universals_name_target_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_NAMES = {'event-type.a': {'spurious': 'property-a'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_universals_description_source_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_DESCRIPTIONS = {'event-type.a': {'property-a': 'spurious'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_universals_description_target_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_DESCRIPTIONS = {'event-type.a': {'spurious': 'property-a'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_universals_container_source_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_CONTAINERS = {'event-type.a': {'property-a': 'spurious'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_spurious_property_universals_container_target_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_UNIVERSALS_CONTAINERS = {'event-type.a': {'spurious': 'property-a'}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        dict(factory.generate_event_types())


def test_property_concept_attribute_wrong_concept_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(factory).TYPE_PROPERTY_ATTRIBUTES = {
        'event-type.a': {'property-a': {'concept-b': ['object-type.string:attr']}}
    }
    with pytest.raises(ValueError, match='concept is not associated with the property'):
        dict(factory.generate_event_types())


@pytest.mark.parametrize("factory", [(create_factory('event-type.a', 'event-type.b'))])
def test_spurious_child_type_exception(factory):
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(factory).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(factory).PARENTS_CHILDREN = [['spurious-parent', 'of', 'event-type.a']]
    with pytest.raises(ValueError):
        dict(factory.generate_event_types())


@pytest.mark.parametrize("factory", [(create_factory('event-type.a', 'event-type.b'))])
def test_spurious_sibling_type_exception(factory):
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(factory).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(factory).CHILDREN_SIBLINGS = [['spurious-sibling', 'of', 'event-type.a']]
    with pytest.raises(ValueError):
        dict(factory.generate_event_types())

# Below we test a variety of other errors in class attributes.


def test_type_without_properties_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {}
    with pytest.raises(ValueError, match='no properties for event type'):
        dict(factory.generate_event_types())


@pytest.mark.parametrize("factory", [(create_factory('event-type.a', 'event-type.b'))])
def test_parent_child_mapping_no_list_exception(factory):
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(factory).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(factory).PARENTS_CHILDREN = [{}]
    with pytest.raises(ValueError, match='not a list'):
        dict(factory.generate_event_types())


@pytest.mark.parametrize("factory", [(create_factory('event-type.a', 'event-type.b'))])
def test_parent_child_mapping_incorrect_length_exception(factory):
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(factory).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(factory).PARENTS_CHILDREN = [[]]
    with pytest.raises(ValueError, match='incorrect number of items'):
        dict(factory.generate_event_types())


@pytest.mark.parametrize("factory", [(create_factory('event-type.a', 'event-type.b'))])
def test_parent_children_siblings_inconsistency_exception(factory):
    type(factory).TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type.string'},
        'event-type.b': {'property-b': 'object-type.string'},
    }
    type(factory).PARENT_MAPPINGS = {'event-type.b': {'property-b': 'property-a'}}
    type(factory).PARENTS_CHILDREN = [['event-type.a', 'of', 'event-type.b']]
    type(factory).CHILDREN_SIBLINGS = [['event-type.b', 'in', 'event-type.b']]
    with pytest.raises(ValueError, match='that event type has no children'):
        dict(factory.generate_event_types())


def test_concept_attribute_no_list_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(factory).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': 'foo'}}}
    with pytest.raises(ValueError, match='not a list'):
        dict(factory.generate_event_types())


def test_invalid_concept_attribute_name_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(factory).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': ['attr']}}}
    with pytest.raises(ValueError, match='does not contain a colon'):
        dict(factory.generate_event_types())

    type(factory).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': []}}}
    with pytest.raises(ValueError, match='not a list of length 1, 2 or 3'):
        dict(factory.generate_event_types())


def test_wrong_concept_attribute_name_exception(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_CONCEPTS = {'event-type.a': {'property-a': {'concept-a': 8}}}
    type(factory).TYPE_PROPERTY_ATTRIBUTES = {'event-type.a': {'property-a': {'concept-a': ['foo:attr']}}}
    with pytest.raises(EDXMLOntologyValidationError, match="must begin with 'object-type.string:'"):
        dict(factory.generate_event_types())


def test_event_type_version_property_is_not_string(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'version': 'object-type.sequence'}}
    type(factory).TYPE_VERSIONS = {'event-type.a': ['version']}
    with pytest.raises(ValueError, match="not a string"):
        dict(factory.generate_event_types())


def test_merge_add_on_single_valued_property(factory):
    type(factory).TYPES = ['event-type.a']
    type(factory).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(factory).TYPE_PROPERTY_MERGE_STRATEGIES = {'event-type.a': {'property-a': EventProperty.MERGE_ADD}}
    with pytest.raises(ValueError, match="not listed in TYPE_MULTI_VALUED_PROPERTIES as a multi-valued property"):
        dict(factory.generate_event_types())
