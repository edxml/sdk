import os

import pytest
from edxml.error import EDXMLValidationError
from edxml.ontology import DataType, Ontology
from edxml.transcode.xml import XmlTranscoderTestHarness, XmlTranscoder


class TestXmlTranscoder(XmlTranscoder):
    """
    This extension of XmlTranscoder allows us to set class attributes
    on it that last for just one unit test, making sure that unit
    tests are free of side effects. Setting class attributes on the
    XmlTranscoder class would cause side effects because that class is
    shared by all tests.
    """
    VERSION = 2
    TYPE_MAP = {'a': 'test-event-type'}
    TYPE_PROPERTIES = {'test-event-type': {'property1': 'object-type.string'}}
    PROPERTY_MAP = {'test-event-type': {'p1': 'property1'}}

    def create_object_types(self):
        self._ontology.create_object_type('object-type.string')
        self._ontology.create_object_type('object-type.integer', data_type=DataType.int().get())


def test_harness_basics():
    harness = XmlTranscoderTestHarness(
        fixtures_path=os.path.dirname(os.path.abspath(__file__)),
        transcoder=TestXmlTranscoder(),
    )

    harness.add_event_source('/test/')
    harness.set_event_source('/test/')
    harness.register('/root/records', TestXmlTranscoder())
    harness.process_xml(filename='test.xml', transcoder_root='/root/records')

    assert repr(harness.events.ontology) == '1 event types, 2 object types, 1 sources and 0 concepts'
    assert len(harness.events) == 1
    assert harness.events[0]['property1'] == {'text'}


def test_harness_event_validation():
    class FailingTranscoder(TestXmlTranscoder):
        TYPE_PROPERTIES = {'test-event-type': {'property1': 'object-type.integer'}}

    harness = XmlTranscoderTestHarness(
        fixtures_path=os.path.dirname(os.path.abspath(__file__)),
        transcoder=FailingTranscoder(),
    )

    harness.add_event_source('/test/')
    harness.set_event_source('/test/')
    harness.register('/root/records', FailingTranscoder())

    # The value of element 'p1' in the XML is not a number while the property
    # data type is. Here we check that the harness validates the transcoder
    # output and a validation exception is raised.
    with pytest.raises(EDXMLValidationError, match='Invalid value for property property1'):
        harness.process_xml(filename='test.xml', transcoder_root='/root/records')


def test_harness_post_processing():
    class FailingTranscoder(TestXmlTranscoder):
        def post_process(self, event, input_record):
            event['property1'] = 'processed'
            yield event

    harness = XmlTranscoderTestHarness(
        fixtures_path=os.path.dirname(os.path.abspath(__file__)),
        transcoder=FailingTranscoder(),
    )

    harness.add_event_source('/test/')
    harness.set_event_source('/test/')
    harness.register('/root/records', FailingTranscoder())

    harness.process_xml(filename='test.xml', transcoder_root='/root/records')

    assert harness.events[0]['property1'] == {'processed'}


def test_harness_element_root_guessing_failure():
    class FailingTranscoder(TestXmlTranscoder):
        TYPE_MAP = {'a': 'test-event-type', 'b': 'another-event-type'}

    harness = XmlTranscoderTestHarness(
        fixtures_path=os.path.dirname(os.path.abspath(__file__)),
        transcoder=FailingTranscoder(),
    )

    with pytest.raises(Exception, match='No element root was specified'):
        harness.process_xml(filename='test.xml', transcoder_root='/root/records')


def test_harness_ontology_upgrade_failure():

    # Create an ontology that is incompatible with
    # the transcoder ontology.
    ontology = Ontology()
    ontology.create_object_type('different-object-type')
    event_type = ontology.create_event_type('test-event-type')
    event_type.create_property('property1', object_type_name='different-object-type')

    harness = XmlTranscoderTestHarness(
        fixtures_path=os.path.dirname(os.path.abspath(__file__)),
        transcoder=TestXmlTranscoder(),
        base_ontology=ontology
    )

    harness.register('/root/records', TestXmlTranscoder())

    with pytest.raises(EDXMLValidationError, match='not compatible'):
        harness.close()


def test_harness_invalid_base_ontology():

    # Create an ontology that is invalid.
    ontology = Ontology()
    ontology.create_object_type('invalid-object-type', data_type='nonsense')

    harness = XmlTranscoderTestHarness(
        fixtures_path=os.path.dirname(os.path.abspath(__file__)),
        transcoder=TestXmlTranscoder(),
        base_ontology=ontology
    )

    harness.register('/root/records', TestXmlTranscoder())

    with pytest.raises(Exception, match='test harness is not valid'):
        harness.close()
