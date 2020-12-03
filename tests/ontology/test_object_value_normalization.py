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

from datetime import datetime

import pytest
from edxml.error import EDXMLValidationError
from edxml.ontology import DataType


def test_normalize_datetime():
    assert DataType.datetime().normalize_objects({'1978-06-17'}) == {'1978-06-17T00:00:00.000000Z'}
    assert DataType.datetime().normalize_objects({datetime(1978, 6, 17)}) == {'1978-06-17T00:00:00.000000Z'}

    with pytest.raises(EDXMLValidationError):
        DataType.datetime().normalize_objects({'foo'})


def test_normalize_number_integer():

    integer_types = [
        DataType.tiny_int(),
        DataType.small_int(),
        DataType.medium_int(),
        DataType.int(),
        DataType.big_int(),
    ]

    for integer_type in integer_types:
        assert integer_type.normalize_objects({2}) == {'2'}
        assert integer_type.normalize_objects({'2'}) == {'2'}
        with pytest.raises(EDXMLValidationError):
            integer_type.normalize_objects({'foo'})


def test_normalize_number_float():

    for float_type in [DataType.float(), DataType.double()]:
        assert float_type.normalize_objects({1.0}) == {'1.000000E+000'}
        assert float_type.normalize_objects({0}) == {'0.000000E+000'}
        assert float_type.normalize_objects({'0.000000E+001'}) == {'0.000000E+000'}
        assert float_type.normalize_objects({'-0.000000E+000'}) == {'0.000000E+000'}
        assert float_type.normalize_objects({'+0.000000E+000'}) == {'0.000000E+000'}
        assert float_type.normalize_objects({'1.000000E+0'}) == {'1.000000E+000'}
        assert float_type.normalize_objects({'01.000000E+0'}) == {'1.000000E+000'}
        assert float_type.normalize_objects({'1E+000'}) == {'1.000000E+000'}
        assert float_type.normalize_objects({'1'}) == {'1.000000E+000'}
        with pytest.raises(EDXMLValidationError):
            float_type.normalize_objects({'foo'})


def test_normalize_decimal():
    assert DataType.decimal(4, 2).normalize_objects({1}) == {'1.00'}
    assert DataType.decimal(4, 2).normalize_objects({1.1}) == {'1.10'}
    assert DataType.decimal(4, 2).normalize_objects({'1'}) == {'1.00'}
    assert DataType.decimal(4, 2).normalize_objects({'01'}) == {'1.00'}
    assert DataType.decimal(4, 2).normalize_objects({'+1'}) == {'1.00'}

    with pytest.raises(EDXMLValidationError):
        DataType.decimal(4, 2).normalize_objects({'foo'})


def test_normalize_currency():
    assert DataType.currency().normalize_objects({1}) == {'1.0000'}
    assert DataType.currency().normalize_objects({1.1}) == {'1.1000'}
    assert DataType.currency().normalize_objects({'1'}) == {'1.0000'}
    assert DataType.currency().normalize_objects({'01'}) == {'1.0000'}
    assert DataType.currency().normalize_objects({'+1'}) == {'1.0000'}

    with pytest.raises(EDXMLValidationError):
        DataType.currency().normalize_objects({'foo'})


def test_normalize_hex():
    assert DataType.hex(2).normalize_objects({'AA'}) == {'aa'}

    with pytest.raises(EDXMLValidationError):
        DataType.hex(2).normalize_objects({2})


def test_normalize_uri():
    # Normalization should not touch percent encoded parts.
    assert DataType.uri().normalize_objects({'http:/www.dom%20ain.com'}) == {'http:/www.dom%20ain.com'}

    with pytest.raises(EDXMLValidationError):
        DataType.uri().normalize_objects({2})


def test_normalize_ip():
    assert DataType.ip_v4().normalize_objects({'127.0.0.1'}) == {'127.0.0.1'}
    assert DataType.ip_v6()\
        .normalize_objects({'2001:db8::8a2e:370:7334'}) == {'2001:0db8:0000:0000:0000:8a2e:0370:7334'}

    with pytest.raises(EDXMLValidationError):
        DataType.ip_v4().normalize_objects({'2001:db8::8a2e:370:7334'})

    with pytest.raises(EDXMLValidationError):
        DataType.ip_v6().normalize_objects({'127.0.0.1'})


def test_normalize_geo():
    assert DataType.geo_point().normalize_objects({'-8.2,25.30'}) == {'-8.200000,25.300000'}
    assert DataType.geo_point().normalize_objects({'-08.2,25.30'}) == {'-8.200000,25.300000'}
    assert DataType.geo_point().normalize_objects({'-08.2,+25.30'}) == {'-8.200000,25.300000'}

    with pytest.raises(EDXMLValidationError):
        DataType.geo_point().normalize_objects({'-8.2,null'})

    with pytest.raises(EDXMLValidationError):
        DataType.geo_point().normalize_objects({'0'})


def test_normalize_string():
    assert DataType.string().normalize_objects({'Ab'}) == {'Ab'}
    assert DataType.string(upper_case=False).normalize_objects({'Ab'}) == {'ab'}
    assert DataType.string(lower_case=False).normalize_objects({'Ab'}) == {'AB'}


def test_normalize_base64():
    assert DataType.base64().normalize_objects({'YW55IGNhcm5hbCBwbGVhcw=='}) == {'YW55IGNhcm5hbCBwbGVhcw=='}
    assert DataType.base64().normalize_objects({'YW55IGNhcm5hbCBwbGVhcw'}) == {'YW55IGNhcm5hbCBwbGVhcw=='}

    with pytest.raises(EDXMLValidationError):
        assert DataType.base64().normalize_objects({'z'})


def test_normalize_boolean():
    assert DataType.boolean().normalize_objects({'true'}) == {'true'}
    assert DataType.boolean().normalize_objects({'True'}) == {'true'}
    assert DataType.boolean().normalize_objects({True}) == {'true'}
    assert DataType.boolean().normalize_objects({1}) == {'true'}

    assert DataType.boolean().normalize_objects({'false'}) == {'false'}
    assert DataType.boolean().normalize_objects({'False'}) == {'false'}
    assert DataType.boolean().normalize_objects({False}) == {'false'}
    assert DataType.boolean().normalize_objects({0}) == {'false'}


def test_normalize_uuid():
    assert DataType.uuid()\
        .normalize_objects({'123e4567-e89b-12d3-a456-426614174000'}) == {'123e4567-e89b-12d3-a456-426614174000'}
