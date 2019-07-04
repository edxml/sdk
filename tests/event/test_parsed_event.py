# coding=utf-8
# the line above is required for inline unicode
import hashlib

from lxml import etree

from edxml import SimpleEDXMLWriter, EDXMLPushParser
from edxml.event import EDXMLEvent, ParsedEvent
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


def create_parsed_event(ontology, event):
    writer = SimpleEDXMLWriter()
    writer.add_ontology(ontology)

    edxml_data = writer.add_event(event) + writer.close()

    class TestParser(EDXMLPushParser):
        events = []

        def _parsed_event(self, event):
            self.events.append(event)

    with TestParser() as parser:
        parser.feed(edxml_data)
        events = parser.events

    return events[0]  # type: ParsedEvent


@pytest.fixture
def parsed_event(ontology, sha1_hash):
    return create_parsed_event(
        ontology,
        EDXMLEvent(
            properties={"a": u"🖤"},
            event_type_name="a",
            source_uri="/a/",
        )
    )


def test_direct_instantiation_not_possible():
    with pytest.raises(NotImplementedError):
        ParsedEvent({})
    with pytest.raises(NotImplementedError):
        ParsedEvent.create({})
    with pytest.raises(NotImplementedError):
        ParsedEvent.create_from_xml('event_type', '/event/source/', etree.Element('tag'))


def test_set_non_string_property_value_fails(parsed_event):
    with pytest.raises(ValueError):
        parsed_event["a"] = True


def test_set_non_string_content_fails(parsed_event):
    with pytest.raises(ValueError):
        parsed_event.set_content(True)


def test_object_character_replacement(parsed_event):
    unicode_replacement_character = unichr(0xfffd)

    parsed_event["b"] = ["a", chr(0), "c"]
    assert parsed_event.get_properties() == {
        "a": {u"🖤"},
        "b": {"a", unicode_replacement_character, "c"}
    }

    parsed_event.set_properties({"b": {"a", chr(0), "c"}})
    assert parsed_event.get_properties() == {"b": {"a", unicode_replacement_character, "c"}}


def test_set_invalid_content(parsed_event):
    unicode_replacement_character = unichr(0xfffd)
    parsed_event.set_content(chr(0))
    assert parsed_event.get_content() == unicode_replacement_character


def test_direct_xml_element_manipulation(parsed_event):
    properties = parsed_event.find('{http://edxml.org/edxml}properties')
    prop = etree.SubElement(properties, '{http://edxml.org/edxml}c')
    prop.text = 'd'
    properties.append(prop)
    parsed_event.flush()
    assert parsed_event.get_properties() == {"a": {u"🖤"}, "c": {"d"}}


def test_cast_to_string(parsed_event):
    string = unicode(parsed_event)

    parsed = etree.fromstring(string)

    # Note that ParsedEvent objects are instantiated by lxml and inherit the
    # namespace from the parent document.
    assert parsed.find('{http://edxml.org/edxml}properties/{http://edxml.org/edxml}a').text == u"🖤"
