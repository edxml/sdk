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
from edxml.error import EDXMLValidationError
from edxml.ontology import DataType, Ontology
from edxml.transcode.object import ObjectTranscoderTestHarness, ObjectTranscoder


class TestObjectTranscoder(ObjectTranscoder):
    """
    This extension of ObjectTranscoder allows us to set class attributes
    on it that last for just one unit test, making sure that unit
    tests are free of side effects. Setting class attributes on the
    ObjectTranscoder class would cause side effects because that class is
    shared by all tests.
    """
    __test__ = False

    VERSION = 2
    TYPES = ['test-event-type']
    TYPE_MAP = {'a': 'test-event-type'}
    TYPE_PROPERTIES = {'test-event-type': {'property1': 'object-type.string'}}
    PROPERTY_MAP = {'test-event-type': {'p1': 'property1'}}

    def create_object_types(self):
        self._ontology.create_object_type('object-type.string')
        self._ontology.create_object_type('object-type.integer', data_type=DataType.int().get())


@pytest.fixture()
def fixture_object():
    return {'type': 'a', 'p1': 'text'}


def test_harness_basics(fixture_object):
    harness = ObjectTranscoderTestHarness(
        transcoder=TestObjectTranscoder(),
        record_selector='type'
    )

    harness.process_object(fixture_object)

    assert repr(harness.events.ontology) == '1 event types, 2 object types, 1 sources and 0 concepts'
    assert len(harness.events) == 1
    assert harness.events[0]['property1'] == {'text'}


def test_harness_event_validation(fixture_object):
    class FailingTranscoder(TestObjectTranscoder):
        TYPE_PROPERTIES = {'test-event-type': {'property1': 'object-type.integer'}}

    harness = ObjectTranscoderTestHarness(
        transcoder=FailingTranscoder(),
        record_selector='type'
    )

    # The value of element 'p1' in the object is not a number while the property
    # data type is. Here we check that the harness validates the transcoder
    # output and a validation exception is raised.
    with pytest.raises(EDXMLValidationError, match='Invalid value for property property1'):
        harness.process_object(fixture_object)


def test_harness_post_processing(fixture_object):
    class FailingTranscoder(TestObjectTranscoder):
        def post_process(self, event, input_record):
            event['property1'] = 'processed'
            yield event

    harness = ObjectTranscoderTestHarness(
        transcoder=FailingTranscoder(),
        record_selector='type'
    )

    harness.process_object(fixture_object)

    assert harness.events[0]['property1'] == {'processed'}


def test_harness_element_root_guessing_failure():
    class FailingTranscoder(TestObjectTranscoder):
        TYPE_MAP = {'a': 'test-event-type', 'b': 'another-event-type'}

    harness = ObjectTranscoderTestHarness(
        transcoder=FailingTranscoder(),
        record_selector='type'
    )

    with pytest.raises(Exception, match='No selector was specified'):
        harness.process_object(fixture_object)


def test_harness_ontology_upgrade_failure():

    # Create an ontology that is incompatible with
    # the transcoder ontology.
    ontology = Ontology()
    ontology.create_object_type('different-object-type')
    event_type = ontology.create_event_type('test-event-type')
    event_type.create_property('property1', object_type_name='different-object-type')

    harness = ObjectTranscoderTestHarness(
        transcoder=TestObjectTranscoder(),
        base_ontology=ontology,
        record_selector='type'
    )

    with pytest.raises(EDXMLValidationError, match='not compatible'):
        harness.close()


def test_harness_invalid_base_ontology():

    # Create an ontology that is invalid.
    ontology = Ontology()
    ontology.create_object_type('invalid-object-type', data_type='nonsense')

    harness = ObjectTranscoderTestHarness(
        transcoder=TestObjectTranscoder(),
        record_selector='type',
        base_ontology=ontology
    )

    with pytest.raises(Exception, match='test harness is not valid'):
        harness.close()
