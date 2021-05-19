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

import json
import pytest

from datetime import datetime
from dateutil.parser import parse

from edxml.miner.node import NodeCollection, EventObjectNode
from edxml.miner.result import ConceptAttribute, MinedConceptAttribute, ConceptInstance, MinedConceptInstance, \
    ConceptInstanceCollection, from_json
from edxml.ontology import Ontology, EventType


def attach_concept_property(event_type, name, concept_name):
    prop = event_type.create_property(name, object_type_name='a')
    return prop.identifies(concept_name)


def test_concept_attribute_basics():
    attr = ConceptAttribute(
        name='object.type.name:extension',
        value='value',
        confidence=0.5,
        concept_naming_priority=13,
        concept_names={'foo': 0.3, 'bar': 0.3}
    )

    assert attr.name == 'object.type.name:extension'
    assert attr.value == 'value'
    assert attr.object_type_name == 'object.type.name'
    assert attr.confidence == 0.5
    assert attr.concept_naming_priority == 13
    assert attr.concept_names == {'foo': 0.3, 'bar': 0.3}

    assert repr(attr) == 'object.type.name:extension = value'


def test_mined_concept_attribute_basics():

    o = Ontology()
    o.create_object_type(name='a')
    o.create_concept(name='c1')

    type_a = EventType(o, name='a')

    assoc = attach_concept_property(type_a, name='p1', concept_name='c1')
    assoc.set_concept_naming_priority(13)

    nodes = NodeCollection({
        'n1': EventObjectNode(
            event_id='e1',
            concept_association=assoc,
            object_type_name='a',
            value='value',
            confidence=0.5,
            time_span=[None, None]
        )
    })

    # Pretend that we mined the node
    nodes['n1'].seed_confidences = {'n1': 0.7}

    attr = MinedConceptAttribute(
        name='name',
        value='value',
        nodes=nodes,
        seed_id='n1'
    )

    assert attr.name == 'name'
    assert attr.value == 'value'
    assert attr.confidence == 0.7
    assert attr.concept_naming_priority == 13
    assert attr.concept_names == {'c1': 0.7}


def test_concept_instance_basics():
    attr = ConceptAttribute(
        name='object.type.name:extension',
        value='value',
        confidence=0.5,
        concept_naming_priority=13,
        concept_names={'foo': 0.3},
        confidence_timeline=[(datetime(1978, 6, 17, 13, 14, 15), None, 0.5)]
    )

    concept = ConceptInstance(identifier='a')

    assert concept.id == 'a'
    assert concept.attributes == []

    assert repr(concept) == 'empty concept: empty concept'

    concept.add_attribute(attr)

    assert concept.has_attribute('object.type.name:extension')
    assert concept.get_attributes('object.type.name:extension') == [attr]
    assert concept.get_attributes('object.type.name:extension')[0].confidence_timeline == [
        (datetime(1978, 6, 17, 13, 14, 15), None, 0.5)
    ]

    assert repr(concept) == 'foo: value'

    concept.add_related_concept('b', confidence=0.8)

    assert concept.get_related_concepts() == {'b': 0.8}


def test_concept_instance_name_selection():
    attr = ConceptAttribute(
        name='object.type.name:extension',
        value='value',
        confidence=0.5,
        concept_naming_priority=13,
        concept_names={'foo': 0.3, 'bar': 0.4}
    )

    concept = ConceptInstance(identifier='c')

    concept.add_attribute(attr)

    assert concept.get_best_concept_name() == 'bar'


def test_concept_instance_title_selection():
    attr_a = ConceptAttribute(
        name='object.type.name:extension',
        value='a',
        confidence=0.5,
        concept_naming_priority=13
    )

    attr_b = ConceptAttribute(
        name='object.type.name:extension',
        value='b',
        confidence=0.5,
        concept_naming_priority=14
    )

    concept = ConceptInstance(identifier='c')

    concept.add_attribute(attr_a)
    concept.add_attribute(attr_b)

    # Title should be taken from attribute having
    # highest naming priority
    assert concept.get_instance_title() == 'b'

    attr_c = ConceptAttribute(
        name='object.type.name:extension',
        value='c',
        confidence=0.6,
        concept_naming_priority=14
    )

    concept.add_attribute(attr_c)

    # When a higher confidence attribute is available,
    # it should be used in stead.
    assert concept.get_instance_title() == 'c'


def test_mined_concept_instance_basics():

    o = Ontology()
    o.create_object_type(name='a')
    o.create_concept(name='c1')

    type_a = EventType(o, name='a')

    assoc = attach_concept_property(type_a, name='p1', concept_name='c1')

    nodes = NodeCollection({
        'n1': EventObjectNode(
            event_id='e1',
            concept_association=assoc,
            object_type_name='a',
            value='value',
            confidence=0.5,
            time_span=[datetime(1978, 6, 17, 13, 14, 15), None]
        )
    })

    # Pretend that we mined the node
    nodes['n1'].seed_confidences = {'n1': 0.7}

    concept = MinedConceptInstance(seed_id='n1')

    assert concept.id == 'n1'
    assert concept.attributes == []

    assert repr(concept) == 'empty concept: empty concept'

    # Getting the seed from an empty concept should fail
    with pytest.raises(Exception, match='Seed node missing in concept instance.'):
        concept.get_seed()

    attr = MinedConceptAttribute(
        name='object.type.name:extension',
        value='value',
        nodes=nodes,
        seed_id='n1'
    )

    concept.add_attribute(attr)

    assert concept.get_seed() == nodes['n1']
    assert concept.has_attribute('object.type.name:extension')
    assert concept.get_attributes('object.type.name:extension') == [attr]
    assert concept.get_attributes('object.type.name:extension')[0].confidence_timeline == [
        (datetime(1978, 6, 17, 13, 14, 15), None, 0.7)
    ]

    assert repr(concept) == 'c1: value'


def test_mined_concept_instance_related_concepts():

    o = Ontology()
    o.create_object_type(name='a')
    o.create_concept(name='c1')

    type_a = EventType(o, name='a')

    p1_c1 = attach_concept_property(type_a, name='p1', concept_name='c1')
    p2_c1 = attach_concept_property(type_a, name='p2', concept_name='c1')

    n1 = EventObjectNode(
            event_id='e1',
            concept_association=p1_c1,
            object_type_name='a',
            value='value',
            confidence=0.5,
            time_span=[None, None]
    )

    n2 = EventObjectNode(
            event_id='e1',
            concept_association=p2_c1,
            object_type_name='a',
            value='value',
            confidence=0.5,
            time_span=[None, None]
    )

    nodes = NodeCollection({'n1': n1})

    relation_p1_p2 = type_a.get_properties()['p1'].relate_inter('related to', 'p2')

    # Pretend that we mined the nodes, once
    # using n1 as seed and once using n2 as seed,
    # resulting in two concept instances.
    n1.seed_confidences = {'n1': 0.6}
    n2.seed_confidences = {'n2': 0.7}

    # Link the nodes using the inter-concept relation
    n1.link_relation(n2, relation_p1_p2)

    attr = MinedConceptAttribute(
        name='object.type.name:extension',
        value='value',
        nodes=nodes,
        seed_id='n1'
    )

    concept = MinedConceptInstance(seed_id='n1')

    concept.add_attribute(attr)

    # Now the concept mined from seed n1 should
    # see the concept mined from n2 as a related concept.
    # The confidence is computed from the confidences of
    # both nodes in the inter-concept relation between them.
    # Note the convoluted way to compute 0.6 * 0.7. This is
    # needed due to the rounding errors that it introduces.
    # The assert will not match exactly without it.
    assert concept.get_related_concepts() == {'n2': 1.0 - (1.0 - 0.6 * 0.7)}


def test_concept_instance_collection_basics():
    collection = ConceptInstanceCollection()

    assert collection.concepts == {}
    assert repr(collection) == '0 concepts'

    concept = ConceptInstance(identifier='c')

    collection.append(concept)

    assert collection.concepts == {'c': concept}
    assert repr(collection) == '1 concepts'


collection_json = {
    "concepts": [
        {
            "id": "c1",
            "title": "a",
            "names": {"concept name": 0.7},
            "attributes": [
                {
                    "name": "object.type.name:extension",
                    "value": "a",
                    "confidence": 0.5,
                    "confidence_timeline": [
                        {
                            "start": "1978-06-17T13:14:15",
                            "end": None,
                            "confidence": 0.5
                        }
                    ],
                    "concept_names": {"concept name": 0.7}
                }
            ],
            "related": [{"id": "c2", "confidence": 3}]
        },
        {
            "id": "c2",
            "title": "b",
            "names": {},
            "attributes": [
                {
                    "name": "object.type.name:extension",
                    "value": "b",
                    "confidence": 0.6,
                    "confidence_timeline": [],
                    "concept_names": {}
                }
            ],
            "related": []
        }
    ]
}


def test_concept_instance_collection_to_json():
    collection = ConceptInstanceCollection()

    assert collection.concepts == {}
    assert repr(collection) == '0 concepts'

    attr_a = ConceptAttribute(
        name='object.type.name:extension',
        value='a',
        confidence=0.5,
        confidence_timeline=[[parse('1978-06-17T13:14:15'), None, 0.5]],
        concept_names={'concept name': 0.7},
        concept_naming_priority=13
    )

    attr_b = ConceptAttribute(
        name='object.type.name:extension',
        value='b',
        confidence=0.6,
        confidence_timeline=[],
        concept_naming_priority=14
    )

    concept = ConceptInstance(identifier='c1')
    concept.add_attribute(attr_a)
    concept.add_related_concept('c2', confidence=3)

    collection.append(concept)

    concept = ConceptInstance(identifier='c2')
    concept.add_attribute(attr_b)

    collection.append(concept)

    assert collection.to_json() == json.dumps(collection_json)


def test_concept_instance_collection_from_json():
    assert from_json(json.dumps(collection_json)).to_json() == json.dumps(collection_json)
