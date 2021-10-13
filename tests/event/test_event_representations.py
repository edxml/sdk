# coding=utf-8
# the line above is required for inline unicode
import codecs
import hashlib
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from IPy import IP

from edxml import EventCollection
from edxml.event import EDXMLEvent, ParsedEvent, EventElement
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
    edxml_data = EventCollection([event]).set_ontology(ontology).to_edxml()
    events = EventCollection.from_edxml(edxml_data)
    return events[0]  # type: ParsedEvent


def create_event_element(event):
    return EventElement(
        event.get_properties(),
        event_type_name=event.get_type_name(),
        source_uri=event.get_source_uri(),
        parents=event.get_explicit_parents(),
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
        attachments={'attachment': 'test'}
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


def test_set_property_to_noniterable_fails(event):
    with pytest.raises(TypeError):
        event.set_properties({"a": object()})


def test_set_property_to_bytes(event):
    event["a"] = b'test'
    assert event["a"] == {b'test'}


def test_add_property_object(event):
    event['smiley'].add("☹")
    assert event.get_properties() == {"smiley": {"😀", "☹"}}


def test_update_property_object(event):
    event['smiley'].update(["☹"])
    assert event.get_properties() == {"smiley": {"😀", "☹"}}


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
    assert event_with_explicit_parent.copy().get_explicit_parents() == event_with_explicit_parent.get_explicit_parents()


def test_deepcopy_event_parents(event_with_explicit_parent):
    assert deepcopy(event_with_explicit_parent).get_explicit_parents() == \
           event_with_explicit_parent.get_explicit_parents()


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
    assert event_with_attachment.get_attachments() == {'attachment': 'test'}


def test_set_attachments(event):
    assert event.get_attachments() == {}
    event.set_attachments({'attachment': 'test'})
    assert event.get_attachments() == {'attachment': 'test'}


def test_change_attachments(event):
    event.set_attachments({'attachment': "changed"})
    assert event.get_attachments() == {'attachment': "changed"}


def test_get_attachments_property(event, event_with_attachment):
    assert event.attachments == {}
    assert event_with_attachment.attachments == {'attachment': 'test'}


def test_set_attachments_property(event):
    assert event.attachments == {}
    event.attachments = {'attachment': 'test'}
    assert event.attachments == {'attachment': 'test'}


def test_extend_attachments_property(event):
    assert event.attachments == {}
    event.attachments['attachment'] = 'test'
    assert event.attachments == {'attachment': 'test'}


def test_delete_attachment_from_property(event):
    event.attachments = {'a': 'x', 'b': 'y'}
    del event.attachments['a']
    assert event.attachments == {'b': 'y'}


def test_read_parents(event_with_explicit_parent, sha1_hash):
    assert event_with_explicit_parent.get_explicit_parents() == [sha1_hash]


def test_set_parents(event, sha1_hash):
    assert event.get_explicit_parents() == []
    event.set_parents([sha1_hash])
    assert event.get_explicit_parents() == [sha1_hash]
    event.set_parents([])
    assert event.get_explicit_parents() == []


def test_add_parents(event, sha1_hash, another_sha1_hash):
    assert event.get_explicit_parents() == []
    event.add_parents([sha1_hash])
    assert event.get_explicit_parents() == [sha1_hash]
    event.add_parents([another_sha1_hash])
    assert set(event.get_explicit_parents()) == {sha1_hash, another_sha1_hash}


def test_add_duplicate_parents(event, sha1_hash):
    assert event.get_explicit_parents() == []
    event.add_parents([sha1_hash])
    assert event.get_explicit_parents() == [sha1_hash]
    event.add_parents([sha1_hash])
    assert event.get_explicit_parents() == [sha1_hash]


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


def test_sort_event(event):
    event.set_properties({})
    event['b'] = 'test'
    event['a'] = 'test'

    attachments = OrderedDict()
    attachments['b'] = 'test'
    attachments['a'] = 'test'
    event.set_attachments(attachments)

    assert list(event.get_properties().keys()) == ['b', 'a']
    assert list(event.get_attachments().keys()) == ['b', 'a']

    event.sort()

    assert list(event.get_properties().keys()) == ['a', 'b']
    assert list(event.get_attachments().keys()) == ['a', 'b']


def test_event_without_type(event_without_type):
    assert event_without_type.get_type_name() is None


def test_event_without_source(event_without_source):
    assert event_without_source.get_source_uri() is None
