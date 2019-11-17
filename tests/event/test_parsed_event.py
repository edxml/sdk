# coding=utf-8
# the line above is required for inline unicode
import hashlib
from collections import OrderedDict

from lxml import etree

from edxml import EventCollection
from edxml.event import EDXMLEvent, ParsedEvent
from edxml.ontology import Ontology
import pytest

namespaces = {'e': 'http://edxml.org/edxml'}


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
        ParsedEvent.create_from_xml(etree.Element('tag'))


def test_set_non_string_property_value_fails(parsed_event):
    with pytest.raises(TypeError):
        parsed_event["a"] = True


def test_set_non_string_content_fails(parsed_event):
    with pytest.raises(ValueError):
        parsed_event.set_attachments({'attachment': True})


def test_object_character_replacement(parsed_event):
    unicode_replacement_character = unichr(0xfffd)

    parsed_event["b"] = [chr(0)]
    b = parsed_event.find('e:properties/e:b', namespaces)
    assert parsed_event.get_properties()["b"] == {unicode_replacement_character}
    assert b.text == unicode_replacement_character

    parsed_event.set_properties({"c": {chr(0)}})
    c = parsed_event.find('e:properties/e:c', namespaces)
    assert parsed_event.get_properties()["c"] == {unicode_replacement_character}
    assert c.text == unicode_replacement_character


def test_set_invalid_content(parsed_event):
    unicode_replacement_character = unichr(0xfffd)
    parsed_event.set_attachments({'attachment': chr(0)})
    assert parsed_event.get_attachments() == {'attachment': unicode_replacement_character}


def test_direct_xml_element_manipulation(parsed_event):
    properties = parsed_event.find('e:properties', namespaces=namespaces)
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
    assert parsed.find('e:properties/e:a', namespaces=namespaces).text == u"🖤"


def test_sort_event(parsed_event):
    parsed_event.set_properties({})
    parsed_event['b'] = ['3', '2']
    parsed_event['a'] = ['1']

    attachments = OrderedDict()
    attachments['b'] = 'b'
    attachments['a'] = 'a'
    parsed_event.set_attachments(attachments)

    assert parsed_event.xpath('e:properties/*/text()', namespaces=namespaces) == ['3', '2', '1']
    assert parsed_event.xpath('e:attachments/*/text()', namespaces=namespaces) == ['b', 'a']

    parsed_event.sort()

    assert parsed_event.xpath('e:properties/*/text()', namespaces=namespaces) == ['1', '2', '3']
    assert parsed_event.xpath('e:attachments/*/text()', namespaces=namespaces) == ['a', 'b']


def test_set_property(parsed_event):
    parsed_event["b"] = ["x"]
    assert parsed_event.properties == {"a": {u"🖤"}, "b": {"x"}}
    assert len(parsed_event.findall('e:properties/e:b', namespaces)) == 1
    assert parsed_event.find('e:properties/e:b', namespaces).text == "x"


def test_extend_property(parsed_event):
    parsed_event["b"] = ["x"]
    parsed_event["b"].add("y")
    assert parsed_event.properties == {"a": {u"🖤"}, "b": {"x", "y"}}
    assert len(parsed_event.findall('e:properties/e:b', namespaces)) == 2
    values = {
        parsed_event.findall('e:properties/e:b', namespaces)[0].text,
        parsed_event.findall('e:properties/e:b', namespaces)[1].text
    }
    assert values == {"x", "y"}


def test_delete_property(parsed_event):
    parsed_event["b"] = ["x"]
    assert len(parsed_event.findall('e:properties/e:a', namespaces)) == 1
    assert len(parsed_event.findall('e:properties/e:b', namespaces)) == 1

    del parsed_event["b"]
    assert len(parsed_event.findall('e:properties/e:a', namespaces)) == 1
    assert len(parsed_event.findall('e:properties/e:b', namespaces)) == 0


def test_delete_multi_valued_property(parsed_event):
    parsed_event["b"] = ["x", "y"]
    assert len(parsed_event.findall('e:properties/e:a', namespaces)) == 1
    assert len(parsed_event.findall('e:properties/e:b', namespaces)) == 2

    del parsed_event["b"]
    assert len(parsed_event.findall('e:properties/e:a', namespaces)) == 1
    assert len(parsed_event.findall('e:properties/e:b', namespaces)) == 0


def test_set_attachment(parsed_event):
    parsed_event.set_attachments({"a": "a"})
    assert len(parsed_event.findall('e:attachments/e:a', namespaces)) == 1
    assert parsed_event.find('e:attachments/e:a', namespaces).text == "a"


def test_delete_attachment(parsed_event):
    parsed_event.set_attachments({"a": "a", "b": "b"})
    assert len(parsed_event.findall('e:attachments/*', namespaces)) == 2

    parsed_event.set_attachments({"a": "a"})
    assert len(parsed_event.findall('e:attachments/*', namespaces)) == 1
    assert parsed_event.find('e:attachments/e:a', namespaces).text == "a"


def test_set_event_type(parsed_event):
    assert parsed_event.attrib['event-type'] == "a"
    parsed_event.set_type('b')
    assert parsed_event.attrib['event-type'] == "b"


def test_set_event_source(parsed_event):
    assert parsed_event.attrib['source-uri'] == "/a/"
    parsed_event.set_source('/b/')
    assert parsed_event.attrib['source-uri'] == "/b/"
