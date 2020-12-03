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

import re

import pytest

from lxml import etree


def test_transcode_element_text(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1>text</p1>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'text'}


def test_transcode_element_attribute(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1/@attr': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1 attr="attribute">text</p1>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'attribute'}


def test_multi_valued_property(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1>text1</p1>'
        '      <p1>text2</p1>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'text1', 'text2'}


def test_skip_empty_element_text(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1></p1>'
        '      <p1>text</p1>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'text'}


def test_skip_empty_element_attribute(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1/@attr': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1 attr=""/>'
        '      <p1 attr="attr"/>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'attr'}


def test_skip_empty_ish_element_text(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1': 'property1'}}
    xml_transcoder.EMPTY_VALUES = {'p1': '-'}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1>-</p1>'
        '      <p1>text</p1>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'text'}


def test_skip_empty_ish_element_attribute(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'p1/@attr': 'property1'}}
    xml_transcoder.EMPTY_VALUES = {'p1/@attr': '-'}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1 attr="-"/>'
        '      <p1 attr="attr"/>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'attr'}


def test_invalid_type_xpath_exception(xml_transcoder):
    xml_transcoder.TYPE_MAP = {']': 'test-event-type'}
    element = etree.fromstring('<root/>')
    with pytest.raises(ValueError, match='invalid XPath for event type'):
        list(xml_transcoder().generate(element, 'a'))


def test_invalid_property_xpath_exception(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {']': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a/>'
        '  </records>'
        '</root>'
    )
    with pytest.raises(ValueError, match='invalid XPath for property'):
        list(xml_transcoder().generate(element.find('records'), 'a'))


def test_normalize_element_text(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'ws_normalize(p)': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p> some  text </p>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'some text'}


def test_extract_patterns_from_element_text(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'findall(p, "[\\d]+")': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p>1,2,3</p>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'1', '2', '3'}


def test_extract_patterns_from_element_text_with_options(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'findall(p, "[a-z]+", %d)' % re.IGNORECASE: 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p>a B c</p>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'a', 'B', 'c'}


def test_strip_control_characters_from_element_text(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'ctrl_strip(p)': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p>a&#13;&#10;b&#13;&#10;c</p>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'abc'}


def test_strip_control_characters_from_element_attribute(xml_transcoder):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type'}
    xml_transcoder.PROPERTY_MAP = {'test-event-type': {'ctrl_strip(p/@attr)': 'property1'}}
    element = etree.fromstring(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p attr="a&#13;&#10;b&#13;&#10;c"/>'
        '    </a>'
        '  </records>'
        '</root>'
    )
    events = list(xml_transcoder().generate(element.find('records'), 'a'))
    assert events[0]['property1'] == {'abc'}
