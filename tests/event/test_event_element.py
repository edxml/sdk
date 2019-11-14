# coding=utf-8
# the line above is required for inline unicode
import hashlib
from collections import OrderedDict

from lxml import etree

from edxml.event import EDXMLEvent, EventElement
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
    event_type.create_property("a", "a")

    return ontology


@pytest.fixture
def event_element(ontology, sha1_hash):
    event = EDXMLEvent(
        properties={"a": u"🖤"},
        event_type_name="a",
        source_uri="/a/",
    )

    return EventElement.create_from_event(event)


def test_set_non_string_property_value_fails(event_element):
    with pytest.raises(TypeError):
        event_element["a"] = True


def test_set_non_string_content_fails(event_element):
    with pytest.raises(ValueError):
        event_element.set_attachments({'attachment': True})


def test_object_character_replacement(event_element):
    unicode_replacement_character = unichr(0xfffd)

    event_element["b"] = [chr(0)]
    assert event_element.get_properties()["b"] == {chr(0)}
    assert event_element.get_element().find('properties/b').text == unicode_replacement_character

    event_element.set_properties({"c": {chr(0)}})
    assert event_element.get_properties() == {"c": {chr(0)}}
    assert event_element.get_element().find('properties/c').text == unicode_replacement_character


def test_set_invalid_content(event_element):
    unicode_replacement_character = unichr(0xfffd)
    event_element.set_attachments({'attachment': chr(0)})
    assert event_element.get_attachments() == {'attachment': unicode_replacement_character}


def test_cast_to_string(event_element):
    string = unicode(event_element)

    parsed = etree.fromstring(string)

    # Note that event elements are meant to be inserted into an
    # EDXML output stream that has a global namespace set. This differs
    # from ParsedEvent instances. These objects are instantiated by lxml
    # and inherit the namespace from their parent document.
    assert parsed.find('properties/a').text == u"🖤"


def test_sort_event(event_element):
    event_element.set_properties({})
    event_element['b'] = ['3', '2']
    event_element['a'] = ['1']

    attachments = OrderedDict()
    attachments['b'] = 'b'
    attachments['a'] = 'a'
    event_element.set_attachments(attachments)

    assert event_element.get_element().xpath('properties/*/text()') == ['3', '2', '1']
    assert event_element.get_element().xpath('attachments/*/text()') == ['b', 'a']

    event_element.sort()

    assert event_element.get_element().xpath('properties/*/text()') == ['1', '2', '3']
    assert event_element.get_element().xpath('attachments/*/text()') == ['a', 'b']
