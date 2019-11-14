# coding=utf-8
# the line above is required for inline unicode
import hashlib
from collections import OrderedDict

from lxml import etree

from edxml import EventCollection
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
    edxml_data = EventCollection([event]).set_ontology(ontology).to_edxml()
    events = EventCollection.from_edxml(edxml_data.encode('utf-8'))
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
    with pytest.raises(TypeError):
        parsed_event["a"] = True


def test_set_non_string_content_fails(parsed_event):
    with pytest.raises(ValueError):
        parsed_event.set_attachments({'attachment': True})


def test_object_character_replacement(parsed_event):
    unicode_replacement_character = unichr(0xfffd)

    parsed_event["b"] = [chr(0)]
    b = parsed_event.find('e:properties/e:b', namespaces={'e': 'http://edxml.org/edxml'})
    assert parsed_event.get_properties()["b"] == {unicode_replacement_character}
    assert b.text == unicode_replacement_character

    parsed_event.set_properties({"c": {chr(0)}})
    c = parsed_event.find('e:properties/e:c', namespaces={'e': 'http://edxml.org/edxml'})
    assert parsed_event.get_properties()["c"] == {unicode_replacement_character}
    assert c.text == unicode_replacement_character


def test_set_invalid_content(parsed_event):
    unicode_replacement_character = unichr(0xfffd)
    parsed_event.set_attachments({'attachment': chr(0)})
    assert parsed_event.get_attachments() == {'attachment': unicode_replacement_character}


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


def test_sort_event(parsed_event):
    parsed_event.set_properties({})
    parsed_event['b'] = ['3', '2']
    parsed_event['a'] = ['1']

    attachments = OrderedDict()
    attachments['b'] = 'b'
    attachments['a'] = 'a'
    parsed_event.set_attachments(attachments)

    namespaces = {'edxml': 'http://edxml.org/edxml'}

    assert parsed_event.xpath('edxml:properties/*/text()', namespaces=namespaces) == ['3', '2', '1']
    assert parsed_event.xpath('edxml:attachments/*/text()', namespaces=namespaces) == ['b', 'a']

    parsed_event.sort()

    assert parsed_event.xpath('edxml:properties/*/text()', namespaces=namespaces) == ['1', '2', '3']
    assert parsed_event.xpath('edxml:attachments/*/text()', namespaces=namespaces) == ['a', 'b']
