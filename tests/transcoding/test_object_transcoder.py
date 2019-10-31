def test_transcode_string_object_attribute(object_transcoder, record):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'attr1': 'property1'}}
    record.attr1 = 'string'
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {'string'}


def test_transcode_integer_object_attribute(object_transcoder, record):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'attr1': 'property1'}}
    record.attr1 = 1
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {1}


def test_transcode_boolean_object_attribute(object_transcoder, record):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'attr1': 'property1'}}
    record.attr1 = True
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {'true'}


def test_transcode_multi_valued_object_attribute(object_transcoder, record):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'attr1': 'property1'}}
    record.attr1 = ['a', 'b']
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {'a', 'b'}


def test_transcode_nonexistent_object_attribute(object_transcoder, record):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'attr1': 'property1'}}
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == set()


def test_transcode_list_item(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {0: 'property1'}}
    record = ['string']
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {'string'}


def test_transcode_nonexistent_list_item(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {0: 'property1'}}
    record = []
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == set()


def test_transcode_dictionary_item(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'key': 'property1'}}
    record = {'key': 'value'}
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {'value'}


def test_transcode_nonexistent_dictionary_item(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'key': 'property1'}}
    record = {}
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == set()


def test_transcode_list_of_dictionaries(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'2.2': 'property1'}}
    record = ['a', 'b', {'1': 'some', '2': 'value'}]
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {'value'}


def test_transcode_dictionary_of_lists(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'a.2': 'property1'}}
    record = {'a': [1, 2, 3]}
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == {3}


def test_transcode_nonexistent_item_in_list_in_dict(object_transcoder):
    type(object_transcoder).TYPE_MAP = {'test_record': 'test-event-type'}
    type(object_transcoder).PROPERTY_MAP = {'test-event-type': {'a.0': 'property1'}}
    record = {'a': []}
    events = list(object_transcoder.generate(record, 'test_record'))
    assert events[0]['property1'] == set()
