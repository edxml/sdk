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

import os
import pytest

from dateutil.parser import parse
from edxml.miner.knowledge import KnowledgeBase
from edxml.miner.parser import KnowledgePullParser, KnowledgePushParser


@pytest.fixture(params=('push', 'pull'))
def knowledge_base(request):
    if request.param == 'pull':
        knowledge = KnowledgeBase()
        parser = KnowledgePullParser(knowledge)
        parser.parse(os.path.dirname(__file__) + '/input.edxml')
    else:
        knowledge = KnowledgeBase()
        parser = KnowledgePushParser(knowledge)
        parser.feed(open(os.path.dirname(__file__) + '/input.edxml', 'rb').read())

    parser.miner.mine()
    return knowledge


@pytest.fixture(params=('start', 'end'))
def knowledge_base_timespan(request):
    if request.param == 'start':
        input_file = os.path.dirname(__file__) + '/input-timespan-start.edxml'
    else:
        input_file = os.path.dirname(__file__) + '/input-timespan-end.edxml'
    knowledge = KnowledgeBase()
    parser = KnowledgePullParser(knowledge)
    parser.parse(input_file)
    parser.miner.mine()
    return knowledge


def test_knowledge_base_basics(knowledge_base):

    empty = KnowledgeBase()
    assert repr(empty) == '0 concepts'

    results = knowledge_base.concept_collection

    assert repr(knowledge_base) == '3 concepts, names, descriptions, containers'
    assert len(results.concepts) == 3

    # Check that we have 4 attributes ('a', 'b', 'c' and 'd')
    attributes = [attr for concept in results.concepts.values() for attr in concept.attributes]
    attribute_repr = [repr(attr) for attr in attributes]

    assert len(attributes) == 4
    assert 'oa: = a' in attribute_repr
    assert 'ob: = b' in attribute_repr
    assert 'oc: = c' in attribute_repr
    assert 'od: = d' in attribute_repr

    # The concept instances that contain attributes 'a' and 'd' are related (in both ways)
    related = [repr(related) for concept in results.concepts.values() for related in concept.get_related_concepts()]

    assert len(related) == 2

    # Check that the attribute confidences are correct. Properties a, c and d should
    # be selected as seeds and have a confidence of 1.0 for that reason.
    # Property a is intra related to b, yielding attribute 'ob:' Its confidence
    # must be computed from just the relation confidence (0.2) and the property
    # confidence of property b (0.8). The concept association confidence (0.9)
    # and property confidence of property a (the seed, 0.7) is irrelevant.
    assert attributes[0].confidence == 1.0
    assert attributes[1].confidence == 1.0 - (1.0 - (0.2 * 0.8))
    assert attributes[2].confidence == 1.0
    assert attributes[3].confidence == 1.0

    # We have one name relation between pa and pb
    assert knowledge_base.get_names_for('ob', 'b') == {'oa': {'a'}}

    # We have one description relation between pa and pc
    assert knowledge_base.get_descriptions_for('oc', 'c') == {'oa': {'a'}}

    # We have one container relation between pa and pd
    assert knowledge_base.get_containers_for('od', 'd') == {'oa': {'a'}}

    time_lines = [attr.confidence_timeline for concept in results.concepts.values() for attr in concept.attributes]

    assert len(time_lines) == 4

    # Verify that all attribute time lines are empty,
    # because the source event has no time information.
    for time_spans in time_lines:
        for time_span in time_spans:
            assert time_span[0] is None
            assert time_span[1] is None


def test_knowledge_base_timespan(knowledge_base_timespan):

    results = knowledge_base_timespan.concept_collection

    assert len(results.concepts) == 3

    time_lines = [attr.confidence_timeline for concept in results.concepts.values() for attr in concept.attributes]

    assert len(time_lines) == 4

    # Verify that all attribute time lines represent a single point in time,
    # because the source event has just one time stamp.
    for time_spans in time_lines:
        for time_span in time_spans:
            assert time_span[0] == parse('1978-06-17T13:14:15Z')
            assert time_span[1] == parse('1978-06-17T13:14:15Z')


def test_filter_concept(knowledge_base):
    assert len(knowledge_base.filter_concept('ca').concept_collection.concepts) == 3
    assert len(knowledge_base.filter_concept('cb').concept_collection.concepts) == 0


def test_filter_attribute(knowledge_base):
    assert len(knowledge_base.filter_attribute('oa:').concept_collection.concepts) == 1
    assert len(knowledge_base.filter_attribute('ob:').concept_collection.concepts) == 1
    assert len(knowledge_base.filter_attribute('oc:').concept_collection.concepts) == 1
    assert len(knowledge_base.filter_attribute('od:').concept_collection.concepts) == 1


def test_filter_related_concepts(knowledge_base):
    # Properties 'pa' and 'pb' have inter-concept relation. Filtering on concepts related
    # to either of these yields the other as result.
    assert len(knowledge_base.filter_related_concepts('obj:0:pa:ca:a').concept_collection.concepts) == 1
    assert len(knowledge_base.filter_related_concepts('obj:0:pb:ca:b').concept_collection.concepts) == 0
    assert len(knowledge_base.filter_related_concepts('obj:0:pc:ca:c').concept_collection.concepts) == 0
    assert len(knowledge_base.filter_related_concepts('obj:0:pd:ca:d').concept_collection.concepts) == 1


def test_to_json(knowledge_base):
    json = knowledge_base.to_json(as_string=False)

    assert json['version'] == '1.0'
    assert json['universals']['names'] == {'ob': {'b': {'oa': ['a']}}}
    assert json['universals']['descriptions'] == {'oc': {'c': {'oa': ['a']}}}
    assert json['universals']['containers'] == {'od': {'d': {'oa': ['a']}}}


def test_from_json(knowledge_base):
    from_json = KnowledgeBase.from_json(knowledge_base.to_json())

    json = from_json.to_json(as_string=False)

    assert json['universals']['names'] == {'ob': {'b': {'oa': ['a']}}}
    assert json['universals']['descriptions'] == {'oc': {'c': {'oa': ['a']}}}
    assert json['universals']['containers'] == {'od': {'d': {'oa': ['a']}}}
