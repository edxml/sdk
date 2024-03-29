"""
This file is automagically imported by pytest and prevents
flake8 from complaining about unused fixtures.
"""
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

from lxml import objectify

from edxml.ontology import DataType
from edxml.transcode import RecordTranscoder
from edxml.transcode.object import ObjectTranscoderMediator
from edxml.transcode.xml import XmlTranscoder


@pytest.fixture()
def record():
    class Record(object):
        pass
    return Record()


@pytest.fixture()
def transcoder():
    class TestTranscoder(RecordTranscoder):
        """
        This extension of RecordTranscoder allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        RecordTranscoder class would cause side effects because that class is
        shared by all tests.
        """
        def create_concepts(self, ontology):
            ontology.create_concept('concept-a', 'concept')

        def create_object_types(self, ontology):
            ontology.create_object_type('object-type.string')
            ontology.create_object_type('object-type.integer', data_type=DataType.int().get())

    return TestTranscoder()


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
        def create_object_types(self, ontology):
            ontology.create_object_type('object-type.string')
            ontology.create_object_type('object-type.integer', data_type=DataType.int().get())

    return TestXmlTranscoder


@pytest.fixture()
def object_transcoder_mediator():
    class TestObjectTranscoderMediator(ObjectTranscoderMediator):
        TYPE_FIELD = 'type'

    return TestObjectTranscoderMediator


def edxml_extract(edxml, path):
    # Below, we remove the EDXML namespace from all
    # tags, allowing us to use simple XPath expressions
    # without namespaces. We can safely do this because
    # our tests do not generate foreign elements.
    for elem in edxml.getiterator():
        if not hasattr(elem.tag, 'find'):
            continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    objectify.deannotate(edxml, cleanup_namespaces=True)

    return edxml.xpath(path)
