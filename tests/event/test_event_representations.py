# coding=utf-8
# the line above is required for inline unicode
import hashlib
from collections import OrderedDict
from datetime import datetime
from IPy import IP

from edxml import EventCollection
from edxml.event import EDXMLEvent, ParsedEvent, EventElement
from edxml.ontology import Ontology
import pytest


@pytest.fixture
def sha1_hash():
    return hashlib.sha1("foo").digest().encode("hex")


@pytest.fixture
def another_sha1_hash():
    return hashlib.sha1("bar").digest().encode("hex")


@pytest.fixture
def ontology():
    ontology = Ontology()
    ontology.create_object_type("a")
    ontology.create_event_source("/a/")
    event_type = ontology.create_event_type("a")
    event_type.create_property("smiley", "a")
    event_type.create_attachment("attachment")

    return ontology


def create_parsed_event(ontology, event):
    edxml_data = EventCollection([event]).set_ontology(ontology).to_edxml()
    events = EventCollection.from_edxml(edxml_data.encode('utf-8'))
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
        properties={"smiley": u"😀"},
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
        properties={"smiley": u"😀"},
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


@pytest.fixture(params=('EdxmlEvent', 'ParsedEvent'))
def event_with_explicit_parent(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": u"😀"},
        event_type_name="a",
        source_uri="/a/",
        parents=[sha1_hash]
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    else:
        return create_parsed_event(ontology, edxml_event)


@pytest.fixture(params=('EdxmlEvent', 'ParsedEvent'))
def event_with_foreign_attribute(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": u"😀"},
        event_type_name="a",
        source_uri="/a/"
    ).set_foreign_attributes({'{http://some/namespace}key': 'value'})

    if request.param == 'EdxmlEvent':
        return edxml_event
    else:
        return create_parsed_event(ontology, edxml_event)


# Note that below fixture has no ParsedEvent variant, because
# events without an event type are invalid in EDXML serialization.
# For that reason, these do not exist as ParsedEvent.
@pytest.fixture(params=('EdxmlEvent', 'EventElement'))
def event_without_type(request, ontology, sha1_hash):
    edxml_event = EDXMLEvent(
        properties={"smiley": u"😀"},
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
        properties={"smiley": u"😀"},
        event_type_name="a"
    )

    if request.param == 'EdxmlEvent':
        return edxml_event
    else:
        return create_event_element(edxml_event)


def test_read_properties(event):

    assert len(event) == 1
    assert event.keys() == ["smiley"]
    assert event.values() == [{u"😀"}]
    assert event["smiley"] == {u"😀"}
    assert event.get_any("smiley") == u"😀"
    assert event["nonexistent"] == set()
    assert event.properties.items() == [('smiley', {'😀'})]
    assert event.get_any("nonexistent") is None
    assert event.get_any("nonexistent", "default") == "default"
    assert event["nonexistent"] == set()
    assert "smiley" in event
    assert "nonexistent" not in event
    assert {prop: values for prop, values in event.iteritems()} == {"smiley": {u"😀"}}
    assert event.get_properties() == {"smiley": {u"😀"}}


def test_get_non_string_property_fails(event):
    with pytest.raises(TypeError):
        event.get(None)


def test_set_and_get_property(event):
    event["c"] = ["d"]
    assert event.get_properties() == {"smiley": {u"😀"}, "c": {"d"}}

    event["c"] = ["d", "e"]
    assert event.get_properties() == {"smiley": {u"😀"}, "c": {"d", "e"}}

    event["c"] = ["e"]
    assert event.get_properties() == {"smiley": {u"😀"}, "c": {"e"}}


def test_set_and_get_property_dict(event):
    event["c"] = ["foo"]
    assert event["c"] == {"foo"}

    event["c"] = ["foo", "bar", "bar"]
    assert event["c"] == {"foo", "bar"}

    event["c"] = []
    assert event["c"] == set()


def test_change_and_get_properties(event):
    event["c"] = "d"
    assert event.get_properties() == {"smiley": {u"😀"}, "c": {"d"}}

    event.set_properties({"a": {"1"}, "b": {"2"}})
    assert event.get_properties() == {"a": {"1"}, "b": {"2"}}


def test_change_and_iterate_properties(event):
    event.set_properties({"a": {"1"}, "b": {"2"}})
    assert {prop: values for prop, values in event.iteritems()} == {"a": {"1"}, "b": {"2"}}


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


def test_set_property_to_noniterable_fails(event):
    with pytest.raises(TypeError):
        event.set_properties({"a": object()})


def test_add_property_object(event):
    event['smiley'].add(u"☹")
    assert event.get_properties() == {"smiley": {u"😀", u"☹"}}


def test_update_property_object(event):
    event['smiley'].update([u"☹"])
    assert event.get_properties() == {"smiley": {u"😀", u"☹"}}


def test_add_nonexistent_property_object(event):
    event['nonexistent'].add("value")
    assert event.get_properties() == {"smiley": {u"😀"}, "nonexistent": {"value"}}


def test_add_properties_object(event):
    event.properties['smiley'].add(u"☹")
    assert event.properties == {"smiley": {u"😀", u"☹"}}


def test_update_properties_object(event):
    event.properties['smiley'].update([u"☹"])
    assert event.properties == {"smiley": {u"😀", u"☹"}}


def test_add_nonexistent_properties_object(event):
    event.properties['nonexistent'].add("value")
    assert event.properties == {"smiley": {u"😀"}, "nonexistent": {"value"}}


def test_delete_property(event):
    event.set_properties({"smiley": [u"😀"], "meh": [u"☹"]})

    del event['meh']
    assert event.get_properties() == {"smiley": {u"😀"}}

    del event['nonexistent']
    assert event.get_properties() == {"smiley": {u"😀"}}


def test_copy_property(event):
    source = event
    target = source.copy()

    source.set_properties({"a": {"foo"}})
    target.set_properties({})

    target.copy_properties_from(source, {"a": "copy", "nonexistent": "should be ignored"})
    assert source.get_properties() == {"a": {"foo"}}
    assert target.get_properties() == {"copy": {u"foo"}}


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
    assert event.get_explicit_parents() == [sha1_hash, another_sha1_hash]


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
    hash_hex = hashlib.sha1(
        u'/a/\na\nsmiley:😀\n'.encode('utf-8')
    ).digest().encode('hex')

    assert event.compute_sticky_hash(ontology) == hash_hex


def test_sort_event(event):
    event.set_properties({})
    event['b'] = 'test'
    event['a'] = 'test'

    attachments = OrderedDict()
    attachments['b'] = 'test'
    attachments['a'] = 'test'
    event.set_attachments(attachments)

    assert event.get_properties().keys() == ['b', 'a']
    assert event.get_attachments().keys() == ['b', 'a']

    event.sort()

    assert event.get_properties().keys() == ['a', 'b']
    assert event.get_attachments().keys() == ['a', 'b']


def test_event_without_type(event_without_type):
    assert event_without_type.get_type_name() is None


def test_event_without_source(event_without_source):
    assert event_without_source.get_source_uri() is None
