"""
This file is automagically imported by pytest and prevents
flake8 from complaining about unused fixtures.
"""
import pytest

from edxml.ontology import Ontology, DataType
from edxml.transcode import Transcoder
from edxml.transcode.object import ObjectTranscoderMediator
from edxml.transcode.xml import XmlTranscoder


@pytest.fixture()
def record():
    class Record(object):
        pass
    return Record()


@pytest.fixture()
def transcoder():
    class TestTranscoder(Transcoder):
        """
        This extension of Transcoder allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        Transcoder class would cause side effects because that class is
        shared by all tests.
        """
        pass

    t = TestTranscoder()
    ontology = Ontology()
    ontology.create_concept('concept-a', 'concept')
    ontology.create_object_type('object-type.string')
    ontology.create_object_type('object-type.integer', data_type=DataType.int().get())
    t.set_ontology(ontology)
    return t


@pytest.fixture()
def xml_transcoder():
    class TestXmlTranscoder(XmlTranscoder):
        """
        This extension of XmlTranscoder allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        XmlTranscoder class would cause side effects because that class is
        shared by all tests.
        """
        def create_object_types(self):
            self._ontology.create_object_type('object-type.string')
            self._ontology.create_object_type('object-type.integer', data_type=DataType.int().get())

    return TestXmlTranscoder


@pytest.fixture()
def object_transcoder_mediator():
    class TestObjectTranscoderMediator(ObjectTranscoderMediator):
        TYPE_FIELD = 'type'

    return TestObjectTranscoderMediator


def create_transcoder(*event_type_names):
    """

    Helper function to generate a transcoder for generating
    events of specified event type name(s).

    Args:
        *event_type_names (str):

    Returns:
        edxml.transcode.Transcoder:
    """
    class TestTranscoder(Transcoder):
        """
        This extension of Transcoder allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        Transcoder class would cause side effects because that class is
        shared by all tests.
        """
        pass

    TestTranscoder.TYPE_MAP = {name: name for name in event_type_names}
    TestTranscoder.TYPE_PROPERTIES = {name: {'property-a': 'object-type.string'} for name in event_type_names}
    t = TestTranscoder()
    ontology = Ontology()
    ontology.create_object_type('object-type.string')
    t.set_ontology(ontology)
    return t
