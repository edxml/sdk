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

import codecs
import hashlib

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from IPy import IP
from lxml import etree

from edxml import EventCollection
from edxml.event import EDXMLEvent, EventElement
from edxml.event import ParsedEvent # noqa
from edxml.logger import log
from edxml.ontology import Ontology
import pytest


@pytest.fixture
def sha1_hash():
    return codecs.encode(hashlib.sha1("foo".encode()).digest(), "hex").decode()


@pytest.fixture
def another_sha1_hash():
    return codecs.encode(hashlib.sha1("bar".encode()).digest(), "hex").decode()


@pytest.fixture
def ontology():
    ontology = Ontology()
    ontology.create_object_type("a")
    ontology.create_event_source("/a/")
    event_type = ontology.create_event_type("a")
    event_type.create_property("smiley", "a").make_hashed()
    event_type.create_attachment("attachment")

    return ontology


def create_parsed_event(ontology, event):
    edxml_data = EventCollection([event]).set_ontology(ontology).to_edxml(pretty_print=False)
    events = EventCollection.from_edxml(edxml_data)
    return events[0]  # type: ParsedEvent


def create_event_element(event):
    return EventElement(
        event.get_properties(),
        event_type_name=event.get_type_name(),
        source_uri=event.get_source_uri(),
        parents=event.get_parent_hashes(),
        attachments=event.get_attachments()
    ).set_foreign_attributes(event.get_foreign_attributes())


@pytest.fixture(params=('EdxmlEvent', 'ParsedEvent', 'EventElement'))
def event(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": "😀"},
        event_type_name="a",
        source_uri="/a/",
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    elif request.param == 'EventElement':
        return create_event_element(edxml_event)
    else:
        return create_parsed_event(ontology, edxml_event)


@pytest.fixture(params=('EdxmlEvent', 'ParsedEvent', 'EventElement'))
def event_with_attachment(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": "😀"},
        event_type_name="a",
        source_uri="/a/",
        attachments={'attachment': {'id': 'test'}}
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    elif request.param == 'EventElement':
        return create_event_element(edxml_event)
    else:
        return create_parsed_event(ontology, edxml_event)


@pytest.fixture(params=('EdxmlEvent', 'ParsedEvent', 'EventElement'))
def event_with_explicit_parent(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": "😀"},
        event_type_name="a",
        source_uri="/a/",
        parents=[sha1_hash]
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    elif request.param == 'EventElement':
        return create_event_element(edxml_event)
    else:
        return create_parsed_event(ontology, edxml_event)


@pytest.fixture(params=('EdxmlEvent', 'ParsedEvent', 'EventElement'))
def event_with_foreign_attribute(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": "😀"},
        event_type_name="a",
        source_uri="/a/"
    ).set_foreign_attributes({'{http://some/namespace}key': 'value'})

    if request.param == 'EdxmlEvent':
        return edxml_event
    elif request.param == 'EventElement':
        return create_event_element(edxml_event)
    else:
        return create_parsed_event(ontology, edxml_event)


# Note that below fixture has no ParsedEvent variant, because
# events without an event type are invalid in EDXML serialization.
# For that reason, these do not exist as ParsedEvent.
@pytest.fixture(params=('EdxmlEvent', 'EventElement'))
def event_without_type(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": "😀"},
        source_uri="/a/",
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    else:
        return create_event_element(edxml_event)


# Note that below fixture has no ParsedEvent variant, because
# events without an event source are invalid in EDXML serialization.
# For that reason, these do not exist as ParsedEvent.
@pytest.fixture(params=('EdxmlEvent', 'EventElement'))
def event_without_source(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": "😀"},
        event_type_name="a"
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    else:
        return create_event_element(edxml_event)


def test_read_properties(event):

    assert len(event) == 1
    assert list(event.keys()) == ["smiley"]
    assert list(event.values()) == [{"😀"}]
    assert event["smiley"] == {"😀"}
    assert event.get_any("smiley") == "😀"
    assert event["nonexistent"] == set()
    assert event.properties.items() == [('smiley', {'😀'})]
    assert event.get_any("nonexistent") is None
    assert event.get_any("nonexistent", "default") == "default"
    assert event["nonexistent"] == set()
    assert "smiley" in event
    assert "nonexistent" not in event
    assert {prop: values for prop, values in event.items()} == {"smiley": {"😀"}}
    assert event.get_properties() == {"smiley": {"😀"}}


def test_get_non_string_property_fails(event):
    with pytest.raises(TypeError):
        event.get(None)


def test_set_and_get_property(event):
    event["c"] = ["d"]
    assert event.get_properties() == {"smiley": {"😀"}, "c": {"d"}}

    event["c"] = ["d", "e"]
    assert event.get_properties() == {"smiley": {"😀"}, "c": {"d", "e"}}

    event["c"] = ["e"]
    assert event.get_properties() == {"smiley": {"😀"}, "c": {"e"}}


def test_set_and_get_property_dict(event):
    event["c"] = ["foo"]
    assert event["c"] == {"foo"}

    event["c"] = ["foo", "bar", "bar"]
    assert event["c"] == {"foo", "bar"}

    event["c"] = []
    assert event["c"] == set()


def test_change_and_get_properties(event):
    event["c"] = "d"
    assert event.get_properties() == {"smiley": {"😀"}, "c": {"d"}}

    event.set_properties({"a": {"1"}, "b": {"2"}})
    assert event.get_properties() == {"a": {"1"}, "b": {"2"}}

    event.properties = {"a": {"foo"}}
    assert event.properties == {"a": {"foo"}}


def test_change_and_iterate_properties(event):
    event.set_properties({"a": {"1"}, "b": {"2"}})
    assert {prop: values for prop, values in event.items()} == {"a": {"1"}, "b": {"2"}}


def test_change_and_find_nonexistent_property(event):
    event.set_properties({"a": ["1"], "b": ["2"]})
    assert "nonexistent" not in event


def test_set_property_to_string(event):
    event["a"] = "string"
    assert event["a"] == {"string"}


def test_set_property_to_integer(event):
    event["a"] = 1
    assert event["a"] == {1}


def test_set_property_to_boolean(event):
    event["a"] = True
    assert event["a"] == {True}


def test_set_property_to_float(event):
    event["a"] = 0.1
    assert event["a"] == {0.1}


def test_set_property_to_datetime(event):
    event["a"] = datetime(2013, 9, 30)
    assert event["a"] == {datetime(2013, 9, 30)}


def test_set_property_to_ip(event):
    event["a"] = IP("127.0.0.1")
    assert event["a"] == {IP("127.0.0.1")}

    event["a"] = {IP("127.0.0.1"), IP("192.168.0.1")}
    assert event["a"] == {IP("127.0.0.1"), IP("192.168.0.1")}


def test_set_property_to_bytes(event):
    event["a"] = b'test'
    assert event["a"] == {b'test'}


def test_add_property_object(event):
    event['smiley'].add("☹")
    assert event.get_properties() == {"smiley": {"😀", "☹"}}


def test_remove_property_object(event):
    event['smiley'].remove("😀")
    assert event.get_properties() == {}


def test_discard_property_object(event):
    event['smiley'].discard("😀")
    assert event.get_properties() == {}


def test_clear_property_objects(event):
    event['smiley'].clear()
    assert event.get_properties() == {}


def test_update_property_object(event):
    event['smiley'].update(["☹"])
    assert event.get_properties() == {"smiley": {"😀", "☹"}}


def test_pop_property_object(event):
    popped = event['smiley'].pop()
    assert popped == "😀"
    assert event.get_properties() == {}


def test_add_nonexistent_property_object(event):
    event['nonexistent'].add("value")
    assert event.get_properties() == {"smiley": {"😀"}, "nonexistent": {"value"}}


def test_add_properties_object(event):
    event.properties['smiley'].add("☹")
    assert event.properties == {"smiley": {"😀", "☹"}}


def test_update_properties_object(event):
    event.properties['smiley'].update(["☹"])
    assert event.properties == {"smiley": {"😀", "☹"}}


def test_add_nonexistent_properties_object(event):
    event.properties['nonexistent'].add("value")
    assert event.properties == {"smiley": {"😀"}, "nonexistent": {"value"}}


def test_delete_property(event):
    event.set_properties({"smiley": ["😀"], "meh": ["☹"]})

    del event['meh']
    assert event.get_properties() == {"smiley": {"😀"}}

    del event['nonexistent']
    assert event.get_properties() == {"smiley": {"😀"}}


def test_copy_event_properties(event):
    assert event.copy().properties == event.properties


def test_deepcopy_event_properties(event):
    assert deepcopy(event).properties == event.properties


def test_copy_event_attachments(event_with_attachment):
    assert event_with_attachment.copy().attachments == event_with_attachment.attachments


def test_deepcopy_event_attachments(event_with_attachment):
    assert deepcopy(event_with_attachment).attachments == event_with_attachment.attachments


def test_copy_event_parents(event_with_explicit_parent):
    assert event_with_explicit_parent.copy().get_parent_hashes() == event_with_explicit_parent.get_parent_hashes()


def test_deepcopy_event_parents(event_with_explicit_parent):
    assert deepcopy(event_with_explicit_parent).get_parent_hashes() == \
           event_with_explicit_parent.get_parent_hashes()


def test_copy_event_foreign_attributes(event_with_foreign_attribute):
    assert event_with_foreign_attribute.copy().get_foreign_attributes() == \
           event_with_foreign_attribute.get_foreign_attributes()


def test_deepcopy_event_foreign_attributes(event_with_foreign_attribute):
    assert deepcopy(event_with_foreign_attribute).get_foreign_attributes() == \
           event_with_foreign_attribute.get_foreign_attributes()


def test_copy_property(event):
    source = event
    target = source.copy()

    source.set_properties({"a": {"foo"}})
    target.set_properties({})

    target.copy_properties_from(source, {"a": "copy", "nonexistent": "should be ignored"})
    assert source.get_properties() == {"a": {"foo"}}
    assert target.get_properties() == {"copy": {"foo"}}


def test_copy_property_values(event):
    source = event
    target = source.copy()

    source.set_properties({"a": {"bar"}, "b": {"bar"}})
    target.set_properties({"a": {"foo"}})

    target.copy_properties_from(source, {"a": "a", "nonexistent": "should be ignored"})
    assert source.get_properties() == {"a": {"bar"}, "b": {"bar"}}
    assert target.get_properties() == {"a": {"foo", "bar"}}


def test_move_property(event):
    source = event
    target = source.copy()

    target.set_properties({"a": {"foo"}, "b": {"foo"}})
    source.set_properties({"a": {"bar"}, "b": {"foobar"}})

    target.move_properties_from(source, {"a": "b", "b": "c", "nonexistent": "should be ignored"})
    assert target.get_properties() == {"a": {"foo"}, "b": {"foo", "bar"}, "c": {"foobar"}}
    assert source.get_properties() == {}


def test_move_property_values(event):
    source = event
    target = source.copy()

    source.set_properties({"a": {"bar"}, "b": {"bar"}})
    target.set_properties({"a": {"foo"}})

    target.move_properties_from(source, {"a": "a", "nonexistent": "should be ignored"})
    assert target.get_properties() == {"a": {"bar", "foo"}}
    assert source.get_properties() == {"b": {"bar"}}


def test_get_attachments(event, event_with_attachment):
    assert event.get_attachments() == {}
    assert event_with_attachment.get_attachments() == {'attachment': {'id': 'test'}}


def test_iterate_attachments(event_with_attachment):
    assert list(iter(event_with_attachment.get_attachments())) == ['attachment']


def test_set_attachments(event):
    assert event.get_attachments() == {}
    event.set_attachment('attachment', {'id': 'test'})
    assert event.get_attachments() == {'attachment': {'id': 'test'}}


def test_change_attachments(event):
    event.set_attachment('attachment', {'id': 'changed'})
    assert event.get_attachments() == {'attachment': {'id': 'changed'}}


def test_get_attachments_property(event, event_with_attachment):
    assert event.attachments == {}
    assert event_with_attachment.attachments == {'attachment': {'id': 'test'}}


def test_set_attachments_property(event):
    assert event.attachments == {}
    event.attachments = {'attachment': {'id': 'test'}}
    assert event.attachments == {'attachment': {'id': 'test'}}


def test_extend_attachments_property(event):
    assert event.attachments == {}
    event.attachments['attachment'] = {'id': 'test'}
    event.attachments['attachment']['id2'] = 'test2'
    assert event.attachments == {'attachment': {'id': 'test', 'id2': 'test2'}}


def test_delete_attachment_from_property(event):
    event.attachments = {'a': {'1': 'x'}, 'b': {'1': 'y', '2': 'z'}}
    del event.attachments['a']
    assert event.attachments == {'b': {'1': 'y', '2': 'z'}}
    del event.attachments['b']['1']
    assert event.attachments == {'b': {'2': 'z'}}


def test_read_parents(event_with_explicit_parent, sha1_hash):
    assert event_with_explicit_parent.get_parent_hashes() == [sha1_hash]


def test_set_parents(event, sha1_hash):
    assert event.get_parent_hashes() == []
    event.set_parents([sha1_hash])
    assert event.get_parent_hashes() == [sha1_hash]
    event.set_parents([])
    assert event.get_parent_hashes() == []


def test_add_parents(event, sha1_hash, another_sha1_hash):
    assert event.get_parent_hashes() == []
    event.add_parents([sha1_hash])
    assert event.get_parent_hashes() == [sha1_hash]
    event.add_parents([another_sha1_hash])
    assert set(event.get_parent_hashes()) == {sha1_hash, another_sha1_hash}


def test_add_duplicate_parents(event, sha1_hash):
    assert event.get_parent_hashes() == []
    event.add_parents([sha1_hash])
    assert event.get_parent_hashes() == [sha1_hash]
    event.add_parents([sha1_hash])
    assert event.get_parent_hashes() == [sha1_hash]


def test_read_foreign_attribute(event_with_foreign_attribute):
    assert event_with_foreign_attribute.get_foreign_attributes() == {'{http://some/namespace}key': 'value'}


def test_write_foreign_attribute(event):
    event.set_foreign_attributes({'{http://some/namespace}key': 'value'})
    assert event.get_foreign_attributes() == {'{http://some/namespace}key': 'value'}


def test_compute_sticky_hash(event, ontology):
    # Note that this test is just to verify that hash
    # computation works for all event types. Exhaustive
    # testing of hash computation is done elsewhere.
    hash_hex = codecs.encode(hashlib.sha1(
        '/a/\na\nsmiley:😀'.encode()
    ).digest(), 'hex').decode()

    event_type = ontology.get_event_type(event.get_type_name())

    assert event.compute_sticky_hash(event_type) == hash_hex


def test_order_sensitivity_properties(event):

    o = Ontology()
    o.create_object_type('a')
    e = o.create_event_type('a')
    e.create_property(name='a', object_type_name='a').make_hashed()
    e.create_property(name='b', object_type_name='a').make_hashed()

    # Create event with lexicographically ordered property keys and values
    # and compute its hash
    properties = OrderedDict()
    properties['a'] = ['test1a', 'test2a']
    properties['b'] = ['test1b', 'test2b']
    event.set_properties(properties)
    event_ordered = event.copy()
    hash_ordered = event.compute_sticky_hash(event_type=e)

    # Set shuffled property keys
    properties = OrderedDict()
    properties['b'] = ['test1b', 'test2b']
    properties['a'] = ['test1a', 'test2a']
    event.set_properties(properties)

    # Event should not be regarded as different or have a different hash
    assert event == event_ordered
    assert event.compute_sticky_hash(event_type=e) == hash_ordered

    # Set shuffled property keys (direct manipulation)
    event.set_properties({})
    event.properties['b'] = ['test1b', 'test2b']
    event.properties['a'] = ['test1a', 'test2a']

    # Event should not be regarded as different or have a different hash
    assert event == event_ordered
    assert event.compute_sticky_hash(event_type=e) == hash_ordered

    # Set shuffled object values
    properties = OrderedDict()
    properties['a'] = ['test2a', 'test1a']
    properties['b'] = ['test2b', 'test1b']
    event.set_properties(properties)

    # Event should not be regarded as different or have a different hash
    assert event == event_ordered
    assert event.compute_sticky_hash(event_type=e) == hash_ordered

    # Set shuffled object values (direct manipulation)
    event.set_properties({})
    event['a'].add('test2a')
    event['a'].add('test1a')
    event['b'].add('test2b')
    event['b'].add('test1b')

    # Event should not be regarded as different or have a different hash
    assert event == event_ordered
    assert event.compute_sticky_hash(event_type=e) == hash_ordered


def test_event_without_type(event_without_type):
    assert event_without_type.get_type_name() is None


def test_event_without_source(event_without_source):
    assert event_without_source.get_source_uri() is None


def test_compare_event_scalar_fails(event):
    with pytest.raises(TypeError):
        assert event == 1


def test_compare_events_differing_types(event):
    other = event.copy()
    assert other == event

    other.set_type('different')
    assert other != event


def test_compare_events_differing_sources(event):
    other = event.copy()
    assert other == event

    other.set_source('/different/')
    assert other != event


def test_compare_events_differing_properties(event):
    other = event.copy()
    assert other == event

    other['empty'] = []
    assert other == event

    other = event.copy()
    other['smiley'].add("☹")
    assert other != event

    other = event.copy()
    other['foo'] = 'bar'
    assert other != event


def test_compare_events_differing_attachments(event):
    other = event.copy()
    assert other == event

    other.attachments['empty'] = []
    assert other == event

    other = event.copy()
    other.attachments['foo'] = 'bar'
    assert other != event

    other = event.copy()
    event.attachments['foo']['bar'] = 'a'
    other.attachments['foo']['bar'] = 'b'
    assert other == event


def test_compare_events_differing_parents(event):
    other = event.copy()
    assert other == event

    other.set_parents(['e9d71f5ee7c92d6dc9e92ffdad17b8bd49418f98'])
    assert other != event


def test_sorted_xml_serialization_properties(event):

    # Create an EDXML event with properties and
    # object values in inverse lexicographical order.
    event.properties = {}
    event.properties['b'] = ['b2', 'b1']
    event.properties['a'] = ['a2', 'a1']

    # Serialize and split into lines
    xml_lines = etree.tostring(event.get_element(), pretty_print=True).splitlines()

    if xml_lines[-1] == b'':
        # ParsedEvent instances have a trailing new line due
        # to the fact that the EDXML writer outputs one EDXML
        # event per line of output.
        xml_lines.pop()

    # Unwrap <event> element
    assert b'<event ' in xml_lines[0]
    assert b'</event>' in xml_lines[-1]

    xml_lines.pop(0)
    xml_lines.pop(-1)

    # Unwrap <properties> element
    assert b'<properties>' in xml_lines[0]
    assert b'</properties>' in xml_lines[-1]

    xml_lines.pop(0)
    xml_lines.pop(-1)

    # Properties and object values in XML serialization
    # should not be sorted.
    assert xml_lines != sorted(xml_lines)

    # Serialize with sorting.
    xml_lines = etree.tostring(event.get_element(sort=True), pretty_print=True).splitlines()[2:-2]

    # Check that serialization is indeed sorted.
    assert xml_lines == sorted(xml_lines)


def test_sorted_xml_serialization_attachments(event):

    # Create an EDXML event with attachments in inverse lexicographical order.
    event.properties = {}
    event.attachments = {}
    event.attachments['b']['2'] = 'b2'
    event.attachments['b']['1'] = 'b1'
    event.attachments['a']['2'] = 'a2'
    event.attachments['a']['1'] = 'a1'

    # Serialize and split into lines
    xml_lines = etree.tostring(event.get_element(), pretty_print=True).splitlines()

    if xml_lines[-1] == b'':
        # ParsedEvent instances have a trailing new line due
        # to the fact that the EDXML writer outputs one EDXML
        # event per line of output.
        xml_lines.pop()

    # Unwrap <event> element
    assert b'<event ' in xml_lines[0]
    assert b'</event>' in xml_lines[-1]

    xml_lines.pop(0)
    xml_lines.pop(-1)

    # Remove <properties/> element
    assert b'<properties/>' in xml_lines[0]
    xml_lines.pop(0)

    # Unwrap <attachments> element
    assert b'<attachments>' in xml_lines[0]
    assert b'</attachments>' in xml_lines[-1]

    xml_lines.pop(0)
    xml_lines.pop(-1)

    # Attachments in XML serialization should not be sorted.
    assert xml_lines != sorted(xml_lines)

    # Serialize with sorting.
    xml_lines = etree.tostring(event.get_element(sort=True), pretty_print=True).splitlines()[3:-2]

    # Check that serialization is indeed sorted.
    assert xml_lines == sorted(xml_lines)


def test_sorted_xml_serialization_parents(event):

    # Create an EDXML event with parent hashes in inverse lexicographical order.
    event.properties = {}
    event.set_parents(['c', 'a', 'b'])

    # Serialize and split into lines
    xml_lines = etree.tostring(event.get_element(), pretty_print=True).splitlines()

    # Parents in XML serialization should not be sorted.
    try:
        assert b'parents="a,b,c"' not in xml_lines[0]
    except AssertionError:
        # We failed to produce unsorted parent hashes. Python sometimes decides to
        # sort the internal set that contains the parent hashes on its own. This
        # varies from one test run to another and also appears to vary between Python
        # versions. So this test is flaky. Even worse, it is flaky in a way that makes
        # retrying the test useless. Once Python decides to output the parents in a
        # particular order, it sticks with it. The best we can do is skip the test in
        # those occasional runs where it decides to sort.
        log.warning('Skipped one test (Python set ordering)')
        return

    # Serialize with sorting.
    xml_lines = etree.tostring(event.get_element(sort=True), pretty_print=True).splitlines()

    # Check that serialization is indeed sorted.
    assert b'parents="a,b,c"' in xml_lines[0]
