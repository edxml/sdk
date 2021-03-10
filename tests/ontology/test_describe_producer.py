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

from edxml.ontology import Ontology
from edxml.ontology.description import describe_producer_rst


def test_describe_basic():
    rst = describe_producer_rst(Ontology(), 'test producer', 'test data')

    assert 'This is a test producer that reads test data' in rst


def test_describe_intra_relations():
    o = Ontology()
    o.create_object_type(name='a', display_name_singular='variety', display_name_plural='varieties')
    o.create_concept(name='c1', display_name_singular='apple')
    o.create_concept(name='c2', display_name_singular='orange')
    o.create_concept(name='c', display_name_singular='building')
    o.create_concept(name='c.d.e', display_name_singular='skyscraper')

    type_a = o.create_event_type(name='a', display_name_singular='apple orangator')

    p1 = type_a.create_property('p1', object_type_name='a')
    p2 = type_a.create_property('p2', object_type_name='a')

    p1.identifies('c1')
    p2.identifies('c2')

    p1.relate_intra('related to', 'p2')

    rst = describe_producer_rst(o, 'test producer', 'test data')

    assert 'This is a test producer that reads test data' in rst
    assert '- buildings as skyscrapers' in rst
    assert '- apples as oranges (using apple orangators)' in rst
    assert ':Apples: Discovering new varieties' in rst
    assert ':Oranges: Discovering new varieties' in rst
    assert '- c (building)' in rst
    assert '- c.d.e (skyscraper)' in rst
    assert '- c1 (apple)\n- c2 (orange)' in rst
    assert '- a (variety)' in rst


def test_describe_inter_relations():
    o = Ontology()
    o.create_object_type(name='a', display_name_singular='variety', display_name_plural='varieties')
    o.create_concept(name='c1', display_name_singular='apple')
    o.create_concept(name='c2', display_name_singular='orange')

    type_a = o.create_event_type(name='a', display_name_singular='apple orangator')

    p3 = type_a.create_property('p3', object_type_name='a')
    p4 = type_a.create_property('p4', object_type_name='a')
    p5 = type_a.create_property('p5', object_type_name='a')
    p6 = type_a.create_property('p6', object_type_name='a')

    p3.identifies('c1')
    p4.identifies('c1')
    p5.identifies('c1')
    p6.identifies('c2')

    p3.relate_inter('related to', 'p4')
    p5.relate_inter('related to', 'p6')

    rst = describe_producer_rst(o, 'test producer', 'test data')

    assert '- Multiple apples to discover interconnected networks (using apple orangators)' in rst
    assert '- Apples to oranges (using apple orangators)' in rst


def test_describe_names_descriptions_containers():
    o = Ontology()
    o.create_object_type(name='value')
    o.create_object_type(name='other')

    type_a = o.create_event_type(name='a', display_name_singular='apple orangator')

    type_a.create_property('p3', object_type_name='other')
    p4 = type_a.create_property('p4', object_type_name='value')
    p5 = type_a.create_property('p5', object_type_name='value')
    p6 = type_a.create_property('p6', object_type_name='value')

    p4.relate_name('p3')
    p5.relate_description('p3')
    p6.relate_container('p3')

    rst = describe_producer_rst(o, 'test producer', 'test data')

    assert 'The test producer provides names for others' in rst
    assert 'The test producer provides descriptions for others' in rst
    assert 'The test producer identifies others as being part of a value' in rst
