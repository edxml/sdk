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

import pytest
from edxml import Template, EDXMLEvent
from edxml.error import EDXMLValidationError
from edxml.ontology import Ontology, DataType


@pytest.fixture()
def event_type():
    o = Ontology()
    o.create_object_type('string')
    o.create_object_type('float', data_type=DataType.float().type)
    o.create_object_type('time', data_type=DataType.datetime().type)
    o.create_object_type('bool', data_type=DataType.boolean().type)
    o.create_object_type('geo', data_type=DataType.geo_point().type)
    event_type = o.create_event_type('a')
    event_type.create_property('p-string', 'string')
    event_type.create_property('p-float', 'float')
    event_type.create_property('p-time-start', 'time')
    event_type.create_property('p-time-end', 'time')
    event_type.create_property('p-url', 'string')
    event_type.create_property('p-bool', 'bool')
    event_type.create_property('p-geo', 'geo')
    return event_type


def test_basic_interpolation(event_type):

    event = EDXMLEvent({'p-string': 'foo'})

    assert Template('Value is [[p-string]].').evaluate(event_type, event) == 'Value is foo.'


def test_colorized_interpolation(event_type):

    event = EDXMLEvent({'p-string': 'foo'})

    assert Template('Value is [[p-string]].')\
        .evaluate(event_type, event, colorize=True) == 'Value is ' + '\x1b[1m\x1b[37m' + 'foo' + '\x1b[0m.'

    event = EDXMLEvent({'p-string': ['foo', 'bar']})

    assert Template('Value is [[p-string]].')\
        .evaluate(event_type, event, colorize=True) in [
        'Value is ' + '\x1b[1m\x1b[37m' + 'foo' + '\x1b[0m' + ' and ' + '\x1b[1m\x1b[37m' + 'bar' + '\x1b[0m.',
        'Value is ' + '\x1b[1m\x1b[37m' + 'bar' + '\x1b[0m' + ' and ' + '\x1b[1m\x1b[37m' + 'foo' + '\x1b[0m.',
    ]


def test_missing_property_collapse(event_type):

    event = EDXMLEvent({})

    assert Template('Value is [[p-string]].').evaluate(event_type, event) == ''


def test_missing_property_scoped_collapse(event_type):

    event = EDXMLEvent({})

    assert Template('Value{ is [[p-string]]}.').evaluate(event_type, event) == 'Value.'
    assert Template('Value{ is{ [[p-string]]} {}}.').evaluate(event_type, event) == 'Value is .'
    assert Template('Value{ is [[p-string]] or {[[p-string]]}.}').evaluate(event_type, event) == 'Value'

    event = EDXMLEvent({'p-float': '1.200000E+000'})

    assert Template('Value is {[[p-float]]{ and [[p-string]]}}.').evaluate(event_type, event) == 'Value is 1.200000.'


def test_render_float(event_type):

    event = EDXMLEvent({'p-float': '1.200000E+000'})

    assert Template('Value is [[p-float]].').evaluate(event_type, event) == 'Value is 1.200000.'


def test_render_datetime(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T23:47:10.123456Z'})

    assert Template('In [[DATETIME:p-time-start,year]].')\
        .evaluate(event_type, event) == 'In 2020.'

    assert Template('In [[DATETIME:p-time-start,month]].')\
        .evaluate(event_type, event) == 'In November 2020.'

    assert Template('On [[DATETIME:p-time-start,date]].')\
        .evaluate(event_type, event) == 'On Wednesday, November 25 2020.'

    assert Template('On [[DATETIME:p-time-start,hour]].')\
        .evaluate(event_type, event) == 'On Wednesday, November 25 2020 at 23h.'

    assert Template('On [[DATETIME:p-time-start,minute]].')\
        .evaluate(event_type, event) == 'On Wednesday, November 25 2020 at 23:47h.'

    assert Template('On [[DATETIME:p-time-start,second]].')\
        .evaluate(event_type, event) == 'On Wednesday, November 25 2020 at 23:47:10h.'

    assert Template('On [[DATETIME:p-time-start,millisecond]].')\
        .evaluate(event_type, event) == 'On Wednesday, November 25 2020 at 23:47:10.123h.'

    assert Template('On [[DATETIME:p-time-start,microsecond]].')\
        .evaluate(event_type, event) == 'On Wednesday, November 25 2020 at 23:47:10.123456h.'


def test_render_time_span(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2020-11-25T14:23:54.000000Z'})

    assert Template('Time span [[TIMESPAN:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'Time span between 2020-11-25 11:47:10+00:00 and 2020-11-25 14:23:54+00:00.'


def test_render_time_span_missing_value(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z'})

    assert Template('Time span [[TIMESPAN:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == ''


def test_render_duration_seconds(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2020-11-25T11:47:12.000000Z'})

    assert Template('It took [[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'It took 2.0 seconds.'


def test_render_duration_minutes(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2020-11-25T11:48:12.000000Z'})

    assert Template('It took [[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'It took 1 minutes and 2 seconds.'


def test_render_duration_hours(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2020-11-25T12:48:12.000000Z'})

    assert Template('It took [[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'It took 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_days(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2020-11-26T12:48:12.000000Z'})

    assert Template('It took [[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'It took 1 days, 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_months(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2020-12-26T12:48:12.000000Z'})

    assert Template('It took [[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'It took 1 months, 1 days, 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_years(event_type):

    event = EDXMLEvent({'p-time-start': '2020-11-25T11:47:10.000000Z', 'p-time-end': '2021-12-26T12:48:12.000000Z'})

    assert Template('It took [[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == 'It took 1 years, 1 months, 1 days, 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_missing_value(event_type):

    event = EDXMLEvent({})

    assert Template('[[DURATION:p-time-start,p-time-end]].')\
        .evaluate(event_type, event) == ''


def test_render_url(event_type):

    event = EDXMLEvent({'p-url': 'http://site.com'})

    assert Template('It can be found [[URL:p-url,here]].')\
        .evaluate(event_type, event) == 'It can be found here (http://site.com).'

    event = EDXMLEvent({})

    assert Template('[[URL:p-url,here]].')\
        .evaluate(event_type, event) == ''


def test_render_merge(event_type):

    event = EDXMLEvent({'p-string': ['a', 'b'], 'p-url': 'c'})

    assert Template('[[MERGE:p-string,p-url]].')\
        .evaluate(event_type, event) in ['a, b and c.', 'b, a and c.']

    event = EDXMLEvent({})

    assert Template('[[MERGE:p-string,p-url]].')\
        .evaluate(event_type, event) == ''


def test_render_country_code(event_type):

    event = EDXMLEvent({'p-string': 'nl'})

    assert Template('[[COUNTRYCODE:p-string]]')\
        .evaluate(event_type, event) == 'Netherlands'


def test_render_boolean_string_choice(event_type):

    event = EDXMLEvent({'p-bool': ['true', 'false']})

    assert Template('[[BOOLEAN_STRINGCHOICE:p-bool,yes,no]]')\
        .evaluate(event_type, event) in ['yes and no', 'no and yes']


def test_render_boolean_on_off(event_type):

    event = EDXMLEvent({'p-bool': ['true', 'false']})

    assert Template('[[BOOLEAN_ON_OFF:p-bool]]')\
        .evaluate(event_type, event) in ['on and off', 'off and on']


def test_render_boolean_is_is_not(event_type):

    event = EDXMLEvent({'p-bool': ['true', 'false']})

    assert Template('[[BOOLEAN_IS_ISNOT:p-bool]]')\
        .evaluate(event_type, event) in ['is and is not', 'is not and is']


def test_render_empty(event_type):

    event = EDXMLEvent({'p-string': 'foo'})

    assert Template('[[EMPTY:p-string,nothing]]')\
        .evaluate(event_type, event) == ''

    event = EDXMLEvent({})

    assert Template('[[EMPTY:p-string,nothing]]')\
        .evaluate(event_type, event) == 'nothing'


def test_render_unless_empty():

    event = EDXMLEvent({})

    assert Template('{Value is {[[p-float]]}{ or [[p-string]]}}.}')\
        .evaluate(event_type, event) == 'Value is .'
    assert Template('{[[UNLESS_EMPTY:p-float,p-string,Value]] is {[[p-float]]}{ or [[p-string]]}.}')\
        .evaluate(event_type, event) == ''


def test_render_geo_point(event_type):

    event = EDXMLEvent({'p-geo': '43.133122,115.734600'})

    assert Template('[[p-geo]]')\
        .evaluate(event_type, event) == '43°7′59 N″ 115°44′4 E″'


def test_validate_unbalanced_brackets(event_type):
    with pytest.raises(EDXMLValidationError, match='Unbalanced curly brackets'):
        Template('{').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='Unbalanced curly brackets'):
        Template('}').validate(event_type)


def test_validate_unknown_property(event_type):
    with pytest.raises(EDXMLValidationError, match='do not exist'):
        Template('[[unknown-property]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='do not exist'):
        Template('[[MERGE:unknown-property]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='do not exist'):
        Template('[[UNLESS_EMPTY:unknown-property,test]]').validate(event_type)


def test_validate_invalid_property(event_type):
    with pytest.raises(EDXMLValidationError, match='cannot be used'):
        Template('[[p-string]]').validate(event_type, property_names=['p-bool'])
    with pytest.raises(EDXMLValidationError, match='cannot be used'):
        Template('[[MERGE:p-string]]').validate(event_type, property_names=['p-bool'])


def test_validate_unknown_formatter(event_type):
    with pytest.raises(EDXMLValidationError, match='Unknown formatter'):
        Template('[[FOO:p-string]]').validate(event_type)


def test_validate_duration_missing_property(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[DURATION:p-time-start]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[DURATION:]]').validate(event_type)


def test_validate_duration_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a datetime'):
        Template('[[DURATION:p-time-start,p-string]]').validate(event_type)


def test_validate_timespan_missing_property(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[TIMESPAN:p-time-start]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[TIMESPAN:]]').validate(event_type)


def test_validate_timespan_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a datetime'):
        Template('[[TIMESPAN:p-time-start,p-string]]').validate(event_type)


def test_validate_datetime_missing_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 2 arguments'):
        Template('[[DATETIME:p-time-start]]').validate(event_type)


def test_validate_datetime_extra_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 2 arguments'):
        Template('[[DATETIME:p-time-start,date,test]]').validate(event_type)


def test_validate_datetime_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a datetime'):
        Template('[[DATETIME:p-string,date]]').validate(event_type)


def test_validate_datetime_wrong_accuracy_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='unknown accuracy option'):
        Template('[[DATETIME:p-time-start,wrong]]').validate(event_type)


def test_validate_url_missing_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 1 properties'):
        Template('[[URL:]]').validate(event_type)


def test_validate_url_extra_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 2 arguments'):
        Template('[[URL:p-url,foo,bar]]').validate(event_type)


def test_validate_merge_missing_property(event_type):
    with pytest.raises(EDXMLValidationError, match='requires at least one property argument'):
        Template('[[MERGE:]]').validate(event_type)


def test_validate_country_code_missing_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 1 properties'):
        Template('[[COUNTRYCODE:]]').validate(event_type)


def test_validate_country_code_extra_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 1 arguments'):
        Template('[[COUNTRYCODE:p-url,foo]]').validate(event_type)


def test_validate_boolean_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a boolean'):
        Template('[[BOOLEAN_STRINGCHOICE:p-string,yes,no]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='not a boolean'):
        Template('[[BOOLEAN_ON_OFF:p-string]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='not a boolean'):
        Template('[[BOOLEAN_IS_ISNOT:p-string]]').validate(event_type)


def test_validate_boolean_string_choice_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 3 arguments'):
        Template('[[BOOLEAN_STRINGCHOICE:p-bool]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='accepts 3 arguments'):
        Template('[[BOOLEAN_STRINGCHOICE:p-bool,yes,no,maybe]]').validate(event_type)


def test_validate_boolean_on_off_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 1 arguments'):
        Template('[[BOOLEAN_ON_OFF:p-bool,yes,no]]').validate(event_type)


def test_validate_boolean_is_isnot_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 1 arguments'):
        Template('[[BOOLEAN_IS_ISNOT:p-bool,yes,no]]').validate(event_type)


def test_validate_empty_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 1 properties'):
        Template('[[EMPTY:]]').validate(event_type)


def test_validate_unless_empty_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='requires at least two arguments'):
        Template('[[UNLESS_EMPTY:p-string]]').validate(event_type)
