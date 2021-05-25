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
from edxml import Template
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
    event_type.create_property('p-string', 'string').make_optional()
    event_type.create_property('p-string-multi-valued', 'string').make_optional().make_multivalued()
    event_type.create_property('p-float', 'float').make_optional()
    event_type.create_property('p-time-start', 'time').make_optional()
    event_type.create_property('p-time-end', 'time').make_optional()
    event_type.create_property('p-url', 'string').make_optional()
    event_type.create_property('p-bool', 'bool').make_optional()
    event_type.create_property('p-geo', 'geo').make_optional()
    event_type.create_property('p-optional', 'string').make_optional()
    event_type.create_property('p-mandatory', 'string').make_mandatory()
    return event_type


def test_basic_interpolation(event_type):

    assert Template('Value is [[p-string]].').evaluate(event_type, {'p-string': {'foo'}}, {}) == 'Value is foo.'


def test_colorized_interpolation(event_type):

    assert Template('[[p-string]].').evaluate(
        event_type, {'p-string': {'foo Bar'}}, {}, colorize=True
    ) == '\x1b[1m\x1b[37m' + 'Foo Bar' + '\x1b[0m.'

    assert Template('value is [[p-string]].')\
        .evaluate(event_type, {'p-string': {'foo', 'bar'}}, {}, colorize=True) in [
        'Value is ' + '\x1b[1m\x1b[37m' + 'foo' + '\x1b[0m' + ' and ' + '\x1b[1m\x1b[37m' + 'bar' + '\x1b[0m.',
        'Value is ' + '\x1b[1m\x1b[37m' + 'bar' + '\x1b[0m' + ' and ' + '\x1b[1m\x1b[37m' + 'foo' + '\x1b[0m.',
    ]


def test_get_properties(event_type):
    assert set(Template('Value is [[p-string]] or [[p-bool]].').get_property_names()) == {'p-string', 'p-bool'}


def test_missing_property_collapse(event_type):

    assert Template('Value is [[p-string]].').evaluate(event_type, {}, {}) == ''


def test_missing_property_scoped_collapse(event_type):

    assert Template('Value{ is [[p-string]]}.').evaluate(event_type, {}, {}) == 'Value.'
    assert Template('Value{ is{ [[p-string]]} {}}.').evaluate(event_type, {}, {}) == 'Value is .'
    assert Template('Value{ is [[p-string]] or {[[p-string]]}.}').evaluate(event_type, {}, {}) == 'Value'
    assert Template('Value is {[[p-float]]{ and [[p-string]]}}.').evaluate(
        event_type, {'p-float': {'1.200000E+000'}}, {}
    ) == 'Value is 1.200000.'


def test_render_float(event_type):

    assert Template('Value is [[p-float]].').evaluate(
        event_type, {'p-float': {'1.200000E+000'}}, {}
    ) == 'Value is 1.200000.'


def test_render_float_invalid(event_type):

    props = {'p-float': {'unknown'}}

    with pytest.raises(ValueError):
        Template('Value is [[p-float]]').evaluate(event_type, props, {})

    assert Template('Value is [[p-float]]').evaluate(
        event_type, props, {}, ignore_value_errors=True
    ) == 'Value is unknown'


def test_render_datetime(event_type):

    props = {'p-time-start': {'2020-11-25T23:47:10.123456Z'}}

    assert Template('In [[date_time:p-time-start,year]].')\
        .evaluate(event_type, props, {}) == 'In 2020.'

    assert Template('In [[date_time:p-time-start,month]].')\
        .evaluate(event_type, props, {}) == 'In November 2020.'

    assert Template('On [[date_time:p-time-start,date]].')\
        .evaluate(event_type, props, {}) == 'On Wednesday, November 25 2020.'

    assert Template('On [[date_time:p-time-start,hour]].')\
        .evaluate(event_type, props, {}) == 'On Wednesday, November 25 2020 at 23h.'

    assert Template('On [[date_time:p-time-start,minute]].')\
        .evaluate(event_type, props, {}) == 'On Wednesday, November 25 2020 at 23:47h.'

    assert Template('On [[date_time:p-time-start,second]].')\
        .evaluate(event_type, props, {}) == 'On Wednesday, November 25 2020 at 23:47:10h.'

    assert Template('On [[date_time:p-time-start,millisecond]].')\
        .evaluate(event_type, props, {}) == 'On Wednesday, November 25 2020 at 23:47:10.123h.'

    assert Template('On [[date_time:p-time-start,microsecond]].')\
        .evaluate(event_type, props, {}) == 'On Wednesday, November 25 2020 at 23:47:10.123456h.'

    # Below we test for an issue in the strftime implementation in some older
    # versions of Python where dates before the year 1900 would raise a ValueError.
    # In recent versions this should not happen anymore.

    assert Template('In [[date_time:p-time-start,year]].').evaluate(
        event_type, {'p-time-start': {'1720-11-25T23:47:10.123456Z'}}, {}
    ) == 'In 1720.'


def test_render_datetime_invalid(event_type):

    props = {'p-time-start': {'A long, long time ago'}}

    with pytest.raises(ValueError):
        Template('[[date_time:p-time-start,year]].').evaluate(event_type, props, {})

    assert Template('[[date_time:p-time-start,year]].')\
        .evaluate(event_type, props, {}, ignore_value_errors=True) == 'A long, long time ago.'


def test_render_time_span(event_type):

    assert Template('Time span [[time_span:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2020-11-25T14:23:54.000000Z'}},
        {}
    ) == 'Time span between 2020-11-25 11:47:10+00:00 and 2020-11-25 14:23:54+00:00.'


def test_render_time_span_missing_value(event_type):

    assert Template('Time span [[time_span:p-time-start,p-time-end]].')\
        .evaluate(event_type, {'p-time-start': {'2020-11-25T11:47:10.000000Z'}}, {}) == ''


def test_render_time_span_invalid(event_type):

    props = {'p-time-start': {'start'}, 'p-time-end': {'end'}}

    with pytest.raises(ValueError):
        Template('Time span [[time_span:p-time-start,p-time-end]].').evaluate(event_type, props, {})

    assert Template('Time span [[time_span:p-time-start,p-time-end]].')\
        .evaluate(event_type, props, {}, ignore_value_errors=True) == 'Time span between start and end.'


def test_render_duration_seconds(event_type):

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2020-11-25T11:47:12.000000Z'}},
        {}
    ) == 'It took 2.0 seconds.'


def test_render_duration_minutes(event_type):

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2020-11-25T11:48:12.000000Z'}},
        {}
    ) == 'It took 1 minutes and 2 seconds.'


def test_render_duration_hours(event_type):

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2020-11-25T12:48:12.000000Z'}},
        {}
    ) == 'It took 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_days(event_type):

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2020-11-26T12:48:12.000000Z'}},
        {}
    ) == 'It took 1 days, 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_months(event_type):

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2020-12-26T12:48:12.000000Z'}},
        {}
    ) == 'It took 1 months, 1 days, 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_years(event_type):

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type,
        {'p-time-start': {'2020-11-25T11:47:10.000000Z'}, 'p-time-end': {'2021-12-26T12:48:12.000000Z'}},
        {}
    ) == 'It took 1 years, 1 months, 1 days, 1 hours, 1 minutes and 2 seconds.'


def test_render_duration_invalid(event_type):

    props = {'p-time-start': {'start'}, 'p-time-end': {'end'}}

    with pytest.raises(ValueError):
        Template('It took [[duration:p-time-start,p-time-end]].').evaluate(event_type, props, {})

    assert Template('It took [[duration:p-time-start,p-time-end]].').evaluate(
        event_type, props, {}, ignore_value_errors=True
    ) == 'It took the time that passed between start and end.'


def test_render_duration_missing_value(event_type):

    assert Template('[[duration:p-time-start,p-time-end]].')\
        .evaluate(event_type, {}, {}) == ''


def test_render_url(event_type):

    assert Template('It can be found [[url:p-url,here]].')\
        .evaluate(event_type, {'p-url': {'http://site.com'}}, {}) == 'It can be found here (http://site.com).'

    assert Template('[[url:p-url,here]].')\
        .evaluate(event_type, {}, {}) == ''


def test_render_merge(event_type):

    assert Template('[[merge:p-string,p-url]].')\
        .evaluate(event_type, {'p-string': {'a', 'b'}, 'p-url': {'c'}}, {}) in ['A, b and c.', 'B, a and c.']

    assert Template('[[merge:p-string,p-url]].')\
        .evaluate(event_type, {}, {}) == ''


def test_render_boolean_string_choice(event_type):

    assert Template('[[boolean_string_choice:p-bool,yes,no]]')\
        .evaluate(event_type, {'p-bool': ['true', 'false']}, {}) in ['Yes and no', 'No and yes']


def test_render_boolean_string_choice_invalid(event_type):

    props = {'p-bool': {'invalid'}}

    with pytest.raises(ValueError):
        Template('[[boolean_string_choice:p-bool,yes,no]]').evaluate(event_type, props, {})

    assert Template('[[boolean_string_choice:p-bool,yes,no]]')\
        .evaluate(event_type, props, {}, ignore_value_errors=True) == 'Yes or no'


def test_render_boolean_on_off(event_type):

    assert Template('[[boolean_on_off:p-bool]]')\
        .evaluate(event_type, {'p-bool': {'true', 'false'}}, {}) in ['On and off', 'Off and on']


def test_render_boolean_on_off_invalid(event_type):

    props = {'p-bool': {'invalid'}}

    with pytest.raises(ValueError):
        Template('[[boolean_on_off:p-bool]]').evaluate(event_type, props, {})

    assert Template('[[boolean_on_off:p-bool]]')\
        .evaluate(event_type, props, {}, ignore_value_errors=True) == 'On or off'


def test_render_boolean_is_is_not(event_type):

    assert Template('[[boolean_is_is_not:p-bool]]')\
        .evaluate(event_type, {'p-bool': {'true', 'false'}}, {}) in ['Is and is not', 'Is not and is']


def test_render_boolean_is_is_not_invalid(event_type):

    with pytest.raises(ValueError):
        Template('[[boolean_is_is_not:p-bool]]').evaluate(event_type, {'p-bool': 'invalid'}, {})

    assert Template('[[boolean_is_is_not:p-bool]]')\
        .evaluate(event_type, {'p-bool': {'invalid'}}, {}, ignore_value_errors=True) == 'Is or is not'


def test_render_empty(event_type):

    assert Template('[[empty:p-string,nothing]]')\
        .evaluate(event_type, {'p-string': {'foo'}}, {}) == ''

    assert Template('[[empty:p-string,nothing]]')\
        .evaluate(event_type, {}, {}) == 'Nothing'


def test_render_unless_empty(event_type):

    assert Template('{Value is {[[p-float]]}{ or [[p-string]]}}.}')\
        .evaluate(event_type, {}, {}) == 'Value is .'
    assert Template('{[[unless_empty:p-float,p-string,Value]] is {[[p-float]]}{ or [[p-string]]}.}')\
        .evaluate(event_type, {}, {}) == ''


def test_render_geo_point(event_type):

    assert Template('[[p-geo]]')\
        .evaluate(event_type, {'p-geo': {'43.133122,115.734600'}}, {}) == '43°7′59 N″ 115°44′4 E″'


def test_render_geo_point_invalid(event_type):

    props = {'p-geo': {'invalid'}}

    with pytest.raises(ValueError):
        Template('[[p-geo]]').evaluate(event_type, props, {})

    assert Template('[[p-geo]]').evaluate(event_type, props, {}, ignore_value_errors=True) == 'Invalid'


def test_render_attachment(event_type):

    assert Template('[[attachment:foo]]')\
        .evaluate(event_type, {}, {'foo': {'foo': 'bar'}}) == '\n\nbar\n\n'


def test_validate_unbalanced_brackets(event_type):
    with pytest.raises(EDXMLValidationError, match='Unbalanced curly brackets'):
        Template('{').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='Unbalanced curly brackets'):
        Template('}').validate(event_type)


def test_validate_unknown_property(event_type):
    with pytest.raises(EDXMLValidationError, match='do not exist'):
        Template('[[unknown-property]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='do not exist'):
        Template('[[merge:unknown-property]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='do not exist'):
        Template('[[unless_empty:unknown-property,test]]').validate(event_type)


def test_validate_invalid_property(event_type):
    with pytest.raises(EDXMLValidationError, match='cannot be used'):
        Template('[[p-string]]').validate(event_type, property_names=['p-bool'])
    with pytest.raises(EDXMLValidationError, match='cannot be used'):
        Template('[[merge:p-string]]').validate(event_type, property_names=['p-bool'])


def test_validate_unknown_attachment(event_type):
    with pytest.raises(EDXMLValidationError, match='is not defined'):
        Template('[[attachment:unknown-attachment]]').validate(event_type)


def test_validate_unknown_formatter(event_type):
    with pytest.raises(EDXMLValidationError, match='Unknown formatter'):
        Template('[[FOO:p-string]]').validate(event_type)


def test_validate_duration_missing_property(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[duration:p-time-start]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[duration:]]').validate(event_type)


def test_validate_duration_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a datetime'):
        Template('[[duration:p-time-start,p-string]]').validate(event_type)


def test_validate_timespan_missing_property(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[time_span:p-time-start]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='requires 2 properties'):
        Template('[[time_span:]]').validate(event_type)


def test_validate_timespan_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a datetime'):
        Template('[[time_span:p-time-start,p-string]]').validate(event_type)


def test_validate_datetime_missing_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 2 arguments'):
        Template('[[date_time:p-time-start]]').validate(event_type)


def test_validate_datetime_extra_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 2 arguments'):
        Template('[[date_time:p-time-start,date,test]]').validate(event_type)


def test_validate_datetime_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a datetime'):
        Template('[[date_time:p-string,date]]').validate(event_type)


def test_validate_datetime_wrong_accuracy_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='unknown accuracy option'):
        Template('[[date_time:p-time-start,wrong]]').validate(event_type)


def test_validate_url_missing_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 1 properties'):
        Template('[[url:]]').validate(event_type)


def test_validate_url_extra_argument(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 2 arguments'):
        Template('[[url:p-url,foo,bar]]').validate(event_type)


def test_validate_merge_missing_property(event_type):
    with pytest.raises(EDXMLValidationError, match='requires at least one property argument'):
        Template('[[merge:]]').validate(event_type)


def test_validate_attachment_missing_attachment_name(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 1 arguments, but 0 were specified'):
        Template('[[attachment:]]').validate(event_type)


def test_validate_boolean_wrong_data_type(event_type):
    with pytest.raises(EDXMLValidationError, match='not a boolean'):
        Template('[[boolean_string_choice:p-string,yes,no]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='not a boolean'):
        Template('[[boolean_on_off:p-string]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='not a boolean'):
        Template('[[boolean_is_is_not:p-string]]').validate(event_type)


def test_validate_boolean_string_choice_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 3 arguments'):
        Template('[[boolean_string_choice:p-bool]]').validate(event_type)
    with pytest.raises(EDXMLValidationError, match='accepts 3 arguments'):
        Template('[[boolean_string_choice:p-bool,yes,no,maybe]]').validate(event_type)


def test_validate_boolean_on_off_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 1 arguments'):
        Template('[[boolean_on_off:p-bool,yes,no]]').validate(event_type)


def test_validate_boolean_is_isnot_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='accepts 1 arguments'):
        Template('[[boolean_is_is_not:p-bool,yes,no]]').validate(event_type)


def test_validate_empty_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='requires 1 properties'):
        Template('[[empty:]]').validate(event_type)


def test_validate_unless_empty_wrong_argument_count(event_type):
    with pytest.raises(EDXMLValidationError, match='requires at least two arguments'):
        Template('[[unless_empty:p-string]]').validate(event_type)


def test_generate_collapsed(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-string]]'
        )
    )
    assert results == [
        (set(), 'Some string'),
        ({'p-string'}, '')
    ]

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-string-multi-valued]]'
        )
    )
    assert results == [
        (set(), 'One or more strings'),
        ({'p-string-multi-valued'}, '')
    ]

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-string]] [[p-bool]]'
        )
    )
    assert results == [
        (set(), 'Some string some bool'),
        ({'p-string'}, ''),
        ({'p-bool'}, '')
    ]


def test_generate_collapsed_scopes(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-string]] {[[p-bool]]} {[[p-float]] {[[p-time-start]] [[p-time-end]]}}'
        )
    )
    # Note that we expect the most deeply scoped properties to be omitted first.
    # We put those properties at the end of the template to verify that behaviour.
    # That allows generating as many variants as possible before the template
    # collapses into an empty string.
    assert results == [
        (set(), 'Some string some bool some float some time some time'),
        ({'p-time-start'}, 'Some string some bool some float '),
        ({'p-time-end'}, 'Some string some bool some float '),
        ({'p-bool'}, 'Some string  some float '),
        ({'p-float'}, 'Some string  '),
        ({'p-string'}, '')
    ]


def test_generate_collapsed_mandatory_property(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-optional]] {[[p-optional]]}'
        )
    )
    # Both properties can be omitted. In both cases the
    # template collapses completely.
    assert results == [
        (set(), 'Some string some string'),
        ({'p-optional'}, ''),
        ({'p-optional'}, '')
    ]

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-optional]] {[[p-mandatory]]}'
        )
    )
    # Only one property can be omitted, resulting
    # in the template collapsing.
    assert results == [
        (set(), 'Some string some string'),
        ({'p-optional'}, ''),
    ]

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[p-mandatory]] {[[p-optional]]}'
        )
    )
    # Only the property in the scope can be omitted,
    # resulting in a partial collapse.
    assert results == [
        (set(), 'Some string some string'),
        ({'p-optional'}, 'Some string '),
    ]


def test_generate_collapsed_placeholder_empty(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[empty:p-optional,empty]]'
        )
    )
    # The property can be omitted but this will not
    # trigger a collapse. So, no collapsed evaluated
    # templates should be generated.
    assert results == [(set(), '')]


def test_generate_collapsed_placeholder_unless_empty(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[unless_empty:p-optional,p-mandatory,test]]'
        )
    )
    # One property cannot be omitted so a collapse cannot occur.
    assert results == [(set(), 'Test')]

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[unless_empty:p-string,p-bool,test]]'
        )
    )
    # Only when both properties are empty a collapse can
    # occur.
    assert results == [
        (set(), 'Test'),
        ({'p-string', 'p-bool'}, '')
    ]


def test_generate_collapsed_placeholder_merge(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[merge:p-time-start,p-time-end]]'
        )
    )
    # Both properties can be omitted but only when both are
    # omitted a collapse occurs.
    assert results == [
        (set(), 'Some time and some time'),
        ({'p-time-start', 'p-time-end'}, ''),
    ]

    # When we make one of both mandatory a collapse cannot occur.
    event_type.get_properties()['p-time-start'].make_mandatory()

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[merge:p-time-start,p-time-end]]'
        )
    )

    # Now only one of the two properties can be omitted and
    # a collapse cannot occur.
    assert results == [(set(), 'Some time and some time')]


def test_generate_collapsed_placeholder_boolean_string_choice(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            'Choose [[boolean_string_choice:p-bool,one,the other]]'
        )
    )
    assert results == [
        (set(), 'Choose one or the other'),
        ({'p-bool'}, '')
    ]


def test_generate_collapsed_placeholder_boolean_on_off(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            'The alarm is [[boolean_on_off:p-bool]].'
        )
    )
    assert results == [
        (set(), 'The alarm is on or off.'),
        ({'p-bool'}, '')
    ]


def test_generate_collapsed_placeholder_boolean_is_is_not(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            'The alarm [[boolean_is_is_not:p-bool]] active.'
        )
    )
    assert results == [
        (set(), 'The alarm is or is not active.'),
        ({'p-bool'}, '')
    ]


def test_generate_collapsed_placeholder_geo_point(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            'The shipment is located at [[p-geo]].'
        )
    )
    assert results == [
        (set(), 'The shipment is located at some geo.'),
        ({'p-geo'}, '')
    ]


def test_generate_collapsed_placeholder_date_time(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[date_time:p-time-start,second]]'
        )
    )
    assert results == [
        (set(), 'Some time'),
        ({'p-time-start'}, '')
    ]


def test_generate_collapsed_placeholder_time_span(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[time_span:p-time-start,p-time-end]]'
        )
    )
    # Both properties can be omitted and in both cases
    # the template will collapse.
    assert results == [
        (set(), 'Between some time and some time'),
        ({'p-time-start'}, ''),
        ({'p-time-end'}, ''),
    ]

    # When we make one of both mandatory a collapse can only
    # occur when the other is omitted.
    event_type.get_properties()['p-time-start'].make_mandatory()

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[time_span:p-time-start,p-time-end]]'
        )
    )

    assert results == [
        (set(), 'Between some time and some time'),
        ({'p-time-end'}, ''),
    ]


def test_generate_collapsed_placeholder_duration(event_type):
    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[duration:p-time-start,p-time-end]]'
        )
    )
    # Both properties can be omitted and in both cases
    # the template will collapse.
    assert results == [
        (set(), 'The time that passed between some time and some time'),
        ({'p-time-start'}, ''),
        ({'p-time-end'}, ''),
    ]

    # When we make one of both mandatory a collapse can only
    # occur when the other is omitted.
    event_type.get_properties()['p-time-start'].make_mandatory()

    results = list(
        Template.generate_collapsed_templates(
            event_type,
            '[[duration:p-time-start,p-time-end]]'
        )
    )

    assert results == [
        (set(), 'The time that passed between some time and some time'),
        ({'p-time-end'}, ''),
    ]
