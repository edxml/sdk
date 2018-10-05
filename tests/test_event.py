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


def test_event_valid(ontology, eventtype, eventproperty):
    # Event type does not exist
    e1 = EDXMLEvent({"testeventproperty": ["testvalue"]}, 'nonexistingvalue')
    assert not e1.is_valid(ontology)

    # Event type exists and is valid
    e2 = EDXMLEvent({"testeventproperty": ["testvalue"]}, 'testeventtype')
    assert e2.is_valid(ontology)

    # Event type exists, but value is invalid
    e3 = EDXMLEvent({"testeventproperty": [152]}, 'testeventtype')
    assert not e3.is_valid(ontology)

    # Event type exists, and property is valid, but contains an extra property
    e4 = EDXMLEvent({"testeventproperty": ["testvalue"], "nonexistingproperty": ["value"]}, 'testeventtype')
    assert not e4.is_valid(ontology)


def test_merge_non_unique(ontology, eventtype, eventproperty):
    e1 = EDXMLEvent({"testeventproperty": ["testvalue"]}, 'testeventtype')
    e2 = EDXMLEvent({"testeventproperty": ["testvalue"]}, 'testeventtype')
    e3 = EDXMLEvent({"testeventproperty": ["testvalue2"]}, 'testeventtype')

    # These events are the same
    assert e1.compute_sticky_hash(ontology) == e2.compute_sticky_hash(ontology)
    # but not these
    assert e1.compute_sticky_hash(ontology) != e3.compute_sticky_hash(ontology)

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

    # These events are the same
    assert e1.compute_sticky_hash(ontology) == e2.compute_sticky_hash(ontology)
    # but not these
    assert e1.compute_sticky_hash(ontology) != e3.compute_sticky_hash(ontology)

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


@pytest.fixture
def datetimeobjecttype(ontology):
    return ontology.create_object_type('datetimeobjecttype', data_type='datetime')


@pytest.fixture
def datetimeproperty(eventtype_unique, datetimeobjecttype):
    return eventtype_unique.create_property('datetimeproperty', datetimeobjecttype.get_name()) \
        .set_merge_strategy('max')


def test_event_datetime_valid(ontology, eventtype_unique, datetimeproperty):
    # Incorrect date format
    e1 = EDXMLEvent({'datetimeproperty': ['2018-10-03 15:15:31']}, 'testeventtypeunique')
    assert not e1.is_valid(ontology)
    # Correct date format
    e2 = EDXMLEvent({'datetimeproperty': ['2018-10-03T15:15:32.000000Z']}, 'testeventtypeunique')
    assert e2.is_valid(ontology)


def test_merge_datetime(ontology, eventtype_unique, datetimeproperty):
    # This test case is written to debug a situation where
    # a merge on a datetime with merge strategy 'min' or 'max'
    # fails due to an incorrect split on the data type.
    # The test case fails intentionally in this commit and is fixed in the next commit.
    e1 = EDXMLEvent({'datetimeproperty': ['2018-10-03T15:15:31.000000Z']}, 'testeventtypeunique')
    e2 = EDXMLEvent({'datetimeproperty': ['2018-10-03T15:15:32.000000Z']}, 'testeventtypeunique')
    assert e1.is_valid(ontology)
    assert e2.is_valid(ontology)

    # These events are not the same
    assert e1.compute_sticky_hash(ontology) != e2.compute_sticky_hash(ontology)
    changed = e1.merge_with([e2], ontology)
    assert changed
    assert e1["datetimeproperty"].pop() == '2018-10-03T15:15:32.000000Z'


def test_merge_parents(ontology, objecttype, eventtype_unique, eventproperty_unique):
    parenttype = ontology.create_event_type('parenteventtype')
    parenttype.create_property('parentproperty', objecttype.get_name()) \
        .set_merge_strategy('replace')

    e1 = EDXMLEvent({"testeventpropertyunique": ["testvalue"]}, 'testeventtypeunique')
    e2 = EDXMLEvent({"parentproperty": ["testvalue"]}, 'parenteventtype')

    e3 = EDXMLEvent({"testeventpropertyunique": ["testvalue2"]}, 'testeventtypeunique')
    e4 = EDXMLEvent({"parentproperty": ["testvalue2"]}, 'parenteventtype')

    # They have no parents yet
    assert e1.get_explicit_parents() == []
    assert e3.get_explicit_parents() == []

    # Merging will result in still not having any parents
    copy1 = deepcopy(e1)
    changed1 = copy1.merge_with([deepcopy(e3)], ontology)
    # No change, because of unique events with different values
    assert not changed1
    # but no parents
    assert copy1.get_explicit_parents() == []

    e1.set_parents([e2.compute_sticky_hash(ontology)])
    e3.set_parents([e4.compute_sticky_hash(ontology)])

    assert e1.get_explicit_parents() == [e2.compute_sticky_hash(ontology)]

    # merge events with different parents
    copy2 = deepcopy(e1)
    changed2 = copy2.merge_with([deepcopy(e3)], ontology)

    # The parents have changed
    assert changed2
    assert set(copy2.get_explicit_parents()) == set(
        [e2.compute_sticky_hash(ontology), e4.compute_sticky_hash(ontology)])

    # merge events with the same parent
    copy3 = deepcopy(e3)
    copy3.set_parents([e2.compute_sticky_hash(ontology)])
    assert copy3.get_explicit_parents() == [e2.compute_sticky_hash(ontology)]

    # This copy has the same parent
    copy4 = deepcopy(e1)
    assert copy4.get_explicit_parents() == [e2.compute_sticky_hash(ontology)]

    changed3 = copy3.merge_with([copy4], ontology)

    # No change in parents
    assert copy3.get_explicit_parents() == [e2.compute_sticky_hash(ontology)]
    # This checks fails until the next commit, because during writing
    # we discovered a bug where it returned as being changed
    assert not changed3


def test_merge_minmax_datetime(ontology, eventtype_unique, datetimeobjecttype):
    # create a datetime prop with strategy min
    prop = eventtype_unique.create_property('prop', datetimeobjecttype.get_name()).set_merge_strategy('min')

    e1 = EDXMLEvent({'prop': ['2018-10-03T15:15:31.000000Z']}, 'testeventtypeunique')
    e2 = EDXMLEvent({'prop': ['2018-10-03T15:15:32.000000Z']}, 'testeventtypeunique')
    e3 = EDXMLEvent({'prop': ['2018-10-03T15:15:30.000000Z']}, 'testeventtypeunique')

    # test the merge with min
    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3], ontology)
    assert changed
    assert copy['prop'].pop() == '2018-10-03T15:15:30.000000Z'

    # set to max
    prop.set_merge_strategy('max')

    # test the merge with max
    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3], ontology)
    assert changed
    assert copy['prop'].pop() == '2018-10-03T15:15:32.000000Z'


@pytest.fixture(params=['number:float', 'number:double', 'number:decimal:3:2'])
def floatobjecttype(request, ontology):
    return ontology.create_object_type('floatobjecttype', data_type=request.param)


def test_merge_minmax_float(ontology, eventtype_unique, floatobjecttype):
    # create a float prop with strategy min
    prop = eventtype_unique.create_property('prop', floatobjecttype.get_name()).set_merge_strategy('min')

    e1 = EDXMLEvent({'prop': ['3.10']}, 'testeventtypeunique')
    e2 = EDXMLEvent({'prop': ['10.20']}, 'testeventtypeunique')
    e3 = EDXMLEvent({'prop': ['2.09']}, 'testeventtypeunique')

    # test the merge with min
    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3], ontology)
    assert changed
    assert float(copy['prop'].pop()) == 2.09

    # set to max
    prop.set_merge_strategy('max')

    # test the merge with max
    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3], ontology)
    assert changed
    assert float(copy['prop'].pop()) == 10.20


@pytest.fixture(params=['number:tinyint', 'number:smallint', 'number:mediumint', 'number:int', 'number:bigint'])
def intobjecttype(request, ontology):
    return ontology.create_object_type('intobjecttype', data_type=request.param)


def test_merge_minmax_int(ontology, eventtype_unique, intobjecttype):
    # create a float prop with strategy min
    prop = eventtype_unique.create_property('prop', intobjecttype.get_name()).set_merge_strategy('min')

    e1 = EDXMLEvent({'prop': ['3']}, 'testeventtypeunique')
    e2 = EDXMLEvent({'prop': ['10']}, 'testeventtypeunique')
    e3 = EDXMLEvent({'prop': ['2']}, 'testeventtypeunique')

    # test the merge with min
    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3], ontology)
    assert changed
    assert int(copy['prop'].pop()) == 2

    # set to max
    prop.set_merge_strategy('max')

    # test the merge with max
    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3], ontology)
    assert changed
    assert int(copy['prop'].pop()) == 10


def test_merge_add(ontology, eventtype_unique, eventproperty_unique, objecttype):
    eventtype_unique.create_property('testeventproperty', objecttype.get_name()) \
        .set_multi_valued(True) \
        .set_merge_strategy('add')

    e1 = EDXMLEvent({
            'testeventpropertyunique': ["test"],
            'testeventproperty': ["value1"]
        }, 'testeventtypeunique')
    # multivalued
    e2 = EDXMLEvent({
            'testeventpropertyunique': ["test"],
            'testeventproperty': ["value2", "value3", "value4"]
        }, 'testeventtypeunique')
    # same value as above
    e3 = EDXMLEvent({
            'testeventpropertyunique': ["test"],
            'testeventproperty': ["value3"]
        }, 'testeventtypeunique')
    # empty value
    e4 = EDXMLEvent({
            'testeventpropertyunique': ["test"],
            'testeventproperty': []
        }, 'testeventtypeunique')

    copy = deepcopy(e1)
    changed = copy.merge_with([e2, e3, e4], ontology)

    assert changed
    assert copy["testeventpropertyunique"].pop() == "test"
    assert copy["testeventproperty"] == set(["value1", "value2", "value3", "value4"])
