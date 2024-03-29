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
from datetime import datetime
from IPy import IP
from lxml import etree

from edxml.event import EDXMLEvent, EventElement
from edxml.ontology import Ontology
import pytest


@pytest.fixture
def sha1_hash():
    return codecs.encode(hashlib.sha1("foo".encode()).digest(), "hex")


@pytest.fixture
def another_sha1_hash():
    return codecs.encode(hashlib.sha1("bar".encode()).digest(), "hex")


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
    return EventElement(
        properties={"a": "🖤"},
        event_type_name="a",
        source_uri="/a/",
    )


def test_create_from_event():
    event = EDXMLEvent(
        properties={"a": "🖤"},
        event_type_name="a",
        source_uri="/a/",
    )

    event_element = EventElement.create_from_event(event)
    assert event_element == event


def test_set_unsupported_property_value_fails(event_element):
    with pytest.raises(TypeError, match='not a value that can be automatically converted'):
        event_element["a"] = object()


def test_set_non_string_attachment_fails(event_element):
    with pytest.raises(TypeError):
        event_element.set_attachment('attachment', True)


def test_object_character_replacement(event_element):
    unicode_replacement_character = chr(0xfffd)

    event_element.replace_invalid_characters()
    event_element["b"] = [chr(0)]
    assert event_element.get_properties()["b"] == {chr(0)}
    assert event_element.get_element().find('properties/b').text == unicode_replacement_character

    event_element.set_properties({"c": {chr(0)}})
    assert event_element.get_properties() == {"c": {chr(0)}}
    assert event_element.get_element().find('properties/c').text == unicode_replacement_character


def test_coerce_integer_property_object(event_element):
    event_element["b"] = 1
    assert event_element.get_element().find('properties/b').text == "1"


def test_coerce_boolean_property_object(event_element):
    event_element["b"] = True
    assert event_element.get_element().find('properties/b').text == "true"


def test_coerce_float_property_object(event_element):
    event_element["b"] = 0.1
    assert event_element.get_element().find('properties/b').text == "0.1"


def test_coerce_datetime_property_object(event_element):
    event_element["b"] = datetime(2013, 9, 30)
    assert event_element.get_element().find('properties/b').text == "2013-09-30T00:00:00.000000Z"


def test_coerce_ip_property_object(event_element):
    event_element["b"] = IP("127.0.0.1")
    assert event_element.get_element().find('properties/b').text == "127.0.0.1"


def test_coerce_bytes_property_object(event_element):
    event_element["b"] = b'test'
    assert event_element.get_element().find('properties/b').text == u"test"


def test_set_attachment(event_element):
    event_element.set_attachment('attachment', {'id': 'value'})
    assert len(event_element.get_element().findall('attachments/attachment')) == 1
    assert event_element.get_element().find('attachments/attachment').text == 'value'
    assert event_element.get_attachments() == {'attachment': {'id': 'value'}}


def test_set_attachment_property(event_element):
    event_element.attachments['attachment']['id'] = 'value'
    assert event_element.get_element().find('attachments/attachment').text == 'value'
    assert event_element.get_attachments() == {'attachment': {'id': 'value'}}


def test_set_invalid_attachment(event_element):
    unicode_replacement_character = chr(0xfffd)
    event_element.replace_invalid_characters()
    event_element.set_attachment('attachment', {'id': chr(0)})
    assert event_element.get_element().find('attachments/attachment').text == unicode_replacement_character
    assert event_element.get_attachments() == {'attachment': {'id': chr(0)}}


def test_cast_to_string(event_element):
    string = str(event_element)

    parsed = etree.fromstring(string)

    # Note that event elements are meant to be inserted into an
    # EDXML output stream that has a global namespace set. This differs
    # from ParsedEvent instances. These objects are instantiated by lxml
    # and inherit the namespace from their parent document.
    assert parsed.find('properties/a').text == "🖤"


def test_set_property(event_element):
    event_element["b"] = ["x"]
    assert event_element.properties == {"a": {"🖤"}, "b": {"x"}}
    assert len(event_element.get_element().findall('properties/b')) == 1
    assert event_element.get_element().find('properties/b').text == "x"


def test_extend_property(event_element):
    event_element["b"] = ["x"]
    event_element["b"].add("y")
    assert event_element.properties == {"a": {"🖤"}, "b": {"x", "y"}}
    assert len(event_element.get_element().findall('properties/b')) == 2
    values = {
        event_element.get_element().findall('properties/b')[0].text,
        event_element.get_element().findall('properties/b')[1].text
    }
    assert values == {"x", "y"}


def test_delete_property(event_element):
    event_element["b"] = ["x"]
    assert len(event_element.get_element().findall('properties/a')) == 1
    assert len(event_element.get_element().findall('properties/b')) == 1

    del event_element["b"]
    assert len(event_element.get_element().findall('properties/a')) == 1
    assert len(event_element.get_element().findall('properties/b')) == 0


def test_delete_multi_valued_property(event_element):
    event_element["b"] = ["x", "y"]
    assert len(event_element.get_element().findall('properties/a')) == 1
    assert len(event_element.get_element().findall('properties/b')) == 2

    del event_element["b"]
    assert len(event_element.get_element().findall('properties/a')) == 1
    assert len(event_element.get_element().findall('properties/b')) == 0


def test_delete_attachment(event_element):
    event_element.set_attachment('a', 'a')
    event_element.set_attachment('b', 'b')
    assert len(event_element.get_element().findall('attachments/*')) == 2

    event_element.set_attachment('b', None)
    assert len(event_element.get_element().findall('attachments/*')) == 1
    assert event_element.get_element().find('attachments/a').text == "a"


def test_set_event_type(event_element):
    assert event_element.get_element().attrib['event-type'] == "a"
    event_element.set_type('b')
    assert event_element.get_element().attrib['event-type'] == "b"


def test_set_event_source(event_element):
    assert event_element.get_element().attrib['source-uri'] == "/a/"
    event_element.set_source('/b/')
    assert event_element.get_element().attrib['source-uri'] == "/b/"
