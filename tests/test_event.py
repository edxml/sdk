# coding=utf-8
# the line above is required for inline unicode
from edxml.event import EDXMLEvent
from edxml.ontology import Ontology
import pytest
from copy import deepcopy


@pytest.fixture
def ontology():
    return Ontology()


@pytest.fixture
def objecttype(ontology):
    return ontology.create_object_type('testobjecttype')


@pytest.fixture
def eventtype(ontology):
    return ontology.create_event_type('testeventtype')


@pytest.fixture
def eventtype_unique(ontology):
    return ontology.create_event_type('testeventtypeunique')


@pytest.fixture
def eventproperty(eventtype, objecttype):
    return eventtype.create_property('testeventproperty', objecttype.get_name()) \
        .set_merge_strategy('replace')


@pytest.fixture
def eventproperty_unique(eventtype_unique, objecttype):
    return eventtype_unique.create_property('testeventpropertyunique', objecttype.get_name()) \
        .unique()


def test_event_init():
    content = u"Två dagar kvar🎉🎉"
    event = EDXMLEvent({}, event_type_name=None, source_uri=None, parents=None, content=content)

    assert event.get_content() == content


def test_merge_non_unique(ontology, eventtype, eventproperty):
    e1 = EDXMLEvent({"testeventproperty": ["testvalue"]}, 'testeventtype')
    e2 = EDXMLEvent({"testeventproperty": ["testvalue"]}, 'testeventtype')
    e3 = EDXMLEvent({"testeventproperty": ["testvalue2"]}, 'testeventtype')

    e1_copy = deepcopy(e1)
    changed1 = e1.merge_with([e2], ontology)
    assert not changed1
    changed2 = e2.merge_with([e1], ontology)
    assert not changed2
    # non-unique properties will be replaced with a merge because they do not identify the event
    # the following will change the properties
    changed3 = e1.merge_with([e3], ontology)
    assert changed3
    changed4 = e3.merge_with([e1_copy], ontology)
    assert changed4
    assert e1["testeventproperty"].pop() == "testvalue2"


def test_merge_unique(ontology, eventtype_unique, eventproperty_unique):
    e1 = EDXMLEvent({"testeventpropertyunique": ["testvalue"]}, 'testeventtypeunique')
    e2 = EDXMLEvent({"testeventpropertyunique": ["testvalue"]}, 'testeventtypeunique')
    e3 = EDXMLEvent({"testeventpropertyunique": ["testvalue2"]}, 'testeventtypeunique')

    e1_copy = deepcopy(e1)
    changed1 = e1.merge_with([e2], ontology)
    assert not changed1
    changed2 = e2.merge_with([e1], ontology)
    assert not changed2
    # unique properties cannot be replaced with a merge because they uniquely identify an event
    # the following will not change the properties
    changed3 = e1.merge_with([e3], ontology)
    assert not changed3
    changed4 = e3.merge_with([e1_copy], ontology)
    assert not changed4
    assert e1["testeventpropertyunique"].pop() == "testvalue"
