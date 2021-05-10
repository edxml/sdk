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
from decimal import Decimal

import pytest
from IPy import IP

from edxml.error import EDXMLValidationError
from edxml.ontology import DataType


def test_validate_datetime():
    assert DataType.datetime().validate_object_value('1978-06-17T00:00:00.000000Z')
    assert DataType.datetime().validate_object_value(datetime(1978, 6, 17))

    with pytest.raises(EDXMLValidationError, match='Invalid value'):
        DataType.datetime().validate_object_value('1978-06-17')

    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'int'"):
        DataType.datetime().validate_object_value(1978)


def test_validate_number_integer():

    integer_types = [
        DataType.tiny_int(signed=False),
        DataType.small_int(signed=False),
        DataType.medium_int(signed=False),
        DataType.int(signed=False),
        DataType.big_int(signed=False),
    ]

    for integer_type in integer_types:
        assert integer_type.validate_object_value(2)
        assert integer_type.validate_object_value('2')

        with pytest.raises(EDXMLValidationError, match='Invalid value string'):
            integer_type.validate_object_value('foo')
        with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'float'"):
            integer_type.validate_object_value(0.5)
        with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
            integer_type.validate_object_value(True)
        with pytest.raises(EDXMLValidationError, match="value is negative"):
            integer_type.validate_object_value(-1)


def test_validate_number_float():

    for float_type in [DataType.float(signed=False), DataType.double(signed=False)]:
        assert float_type.validate_object_value(1.0)
        assert float_type.validate_object_value(1)
        assert float_type.validate_object_value('0.000000E+000')

        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('-0.000000E+000')
        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('+1.000000E+000')
        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('1.000000e+000')
        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('1.0E+000')
        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('1.000000E+0')
        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('10.000000E+000')
        with pytest.raises(EDXMLValidationError, match="Invalid value string"):
            float_type.validate_object_value('foo')
        with pytest.raises(EDXMLValidationError, match="value is negative"):
            float_type.validate_object_value(-1.0)
        with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
            float_type.validate_object_value(True)


def test_validate_decimal():
    decimal = DataType.decimal(4, 2, signed=False)
    assert decimal.validate_object_value(1)
    assert decimal.validate_object_value(1.1)
    assert decimal.validate_object_value('1.00')
    assert decimal.validate_object_value(Decimal(1))

    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        decimal.validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match='Must have 2 fractional digits'):
        decimal.validate_object_value('1')
    with pytest.raises(EDXMLValidationError, match='Must have 2 fractional digits'):
        decimal.validate_object_value('1.0')
    with pytest.raises(EDXMLValidationError, match='Zero padding of the integral part is not allowed'):
        decimal.validate_object_value('01.00')
    with pytest.raises(EDXMLValidationError, match='Zero must not have any sign'):
        decimal.validate_object_value('-0.00')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        decimal.validate_object_value(True)
    with pytest.raises(EDXMLValidationError, match="Value is negative"):
        decimal.validate_object_value(-1)


def test_validate_currency():
    assert DataType.currency().validate_object_value(1)
    assert DataType.currency().validate_object_value(1.1)
    assert DataType.currency().validate_object_value('1.0000')
    assert DataType.currency().validate_object_value(Decimal(1))

    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.currency().validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match='Must have four fractional digits'):
        DataType.currency().validate_object_value('1.0')
    with pytest.raises(EDXMLValidationError, match='Must have four fractional digits'):
        DataType.currency().validate_object_value('1')
    with pytest.raises(EDXMLValidationError, match='Zero padding of the integral part is not allowed'):
        DataType.currency().validate_object_value('01.0000')
    with pytest.raises(EDXMLValidationError, match='Zero must not have any sign'):
        DataType.currency().validate_object_value('-0.0000')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.currency().validate_object_value(True)


def test_validate_hex():
    assert DataType.hex(1).validate_object_value('aa')
    assert DataType.hex(2, separator=':', group_size=1).validate_object_value('aa:bb')

    with pytest.raises(EDXMLValidationError, match='Must be all lowercase'):
        DataType.hex(1).validate_object_value('AA')
    with pytest.raises(EDXMLValidationError, match='Incorrect length'):
        DataType.hex(1).validate_object_value('aabb')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.hex(1).validate_object_value('gg')
    with pytest.raises(EDXMLValidationError, match='Incorrect length'):
        DataType.hex(2, separator=':', group_size=1).validate_object_value('aa:b')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.hex(2, separator=':', group_size=1).validate_object_value(True)


def test_validate_uri():
    assert DataType.uri().validate_object_value('http:/www.domain.com')
    assert DataType.uri().validate_object_value('foo bar')

    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.uri().validate_object_value(True)


def test_validate_ip():
    assert DataType.ip_v4().validate_object_value('127.0.0.1')
    assert DataType.ip_v4().validate_object_value(IP('127.0.0.1'))
    assert DataType.ip_v6().validate_object_value('2001:0db8:0000:0000:0000:8a2e:0370:7334')
    assert DataType.ip_v6().validate_object_value(IP('2001:0db8:0000:0000:0000:8a2e:0370:7334'))

    with pytest.raises(EDXMLValidationError, match='IP addresses must not be shortened or zero padded'):
        DataType.ip_v4().validate_object_value('127.000.000.001')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.ip_v4().validate_object_value('2001:0db8:0000:0000:0000:8a2e:0370:7334')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.ip_v4().validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.ip_v4().validate_object_value(True)

    with pytest.raises(EDXMLValidationError, match='IP addresses must not be shortened or zero padded'):
        DataType.ip_v6().validate_object_value('2001:db8::8a2e:370:7334')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.ip_v6().validate_object_value('127.0.0.1')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.ip_v6().validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.ip_v6().validate_object_value(True)


def test_validate_geo():
    assert DataType.geo_point().validate_object_value('-8.200000,25.300000')

    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.geo_point().validate_object_value('-8.200000,null')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.geo_point().validate_object_value('-8.200000')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.geo_point().validate_object_value('-8.200000,25')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.geo_point().validate_object_value('-8,25.300000')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.geo_point().validate_object_value('0')
    with pytest.raises(EDXMLValidationError, match='Missing latitude decimals'):
        DataType.geo_point().validate_object_value('-8.2,25.300000')
    with pytest.raises(EDXMLValidationError, match='Missing longitude decimals'):
        DataType.geo_point().validate_object_value('-8.200000,25.3')
    with pytest.raises(EDXMLValidationError, match=r"Longitude has a leading '\+' sign"):
        DataType.geo_point().validate_object_value('-8.200000,+25.300000')
    with pytest.raises(EDXMLValidationError, match=r"Latitude has a leading '\+' sign"):
        DataType.geo_point().validate_object_value('+8.200000,25.300000')
    with pytest.raises(EDXMLValidationError, match=r'Latitude not within range \[-90,90\]'):
        DataType.geo_point().validate_object_value('91.200000,25.300000')
    with pytest.raises(EDXMLValidationError, match=r"Longitude not within range \[-180,180\]"):
        DataType.geo_point().validate_object_value('+8.200000,181.300000')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.geo_point().validate_object_value(True)


def test_validate_string():
    assert DataType.string().validate_object_value('Ab')
    assert DataType.string().validate_object_value('😀')
    assert DataType.string(upper_case=False).validate_object_value('ab')
    assert DataType.string(lower_case=False).validate_object_value('AB')

    with pytest.raises(EDXMLValidationError, match='Empty object values are not valid'):
        DataType.string().validate_object_value('')
    with pytest.raises(EDXMLValidationError, match='String is too long'):
        DataType.string(length=1).validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match='String contains non-latin1 characters'):
        DataType.string(require_unicode=False).validate_object_value('😀')
    with pytest.raises(EDXMLValidationError, match='String must be all lowercase'):
        DataType.string(upper_case=False).validate_object_value('A')
    with pytest.raises(EDXMLValidationError, match='String must be all uppercase'):
        DataType.string(lower_case=False).validate_object_value('a')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.string().validate_object_value(True)


def test_validate_base64():
    assert DataType.base64(length=16).validate_object_value('YW55IGNhcm5hbCBwbGVhcw==')

    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.base64().validate_object_value('z')
    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.base64().validate_object_value('YW55IGNhcm5hbCBwbGVhcw')
    with pytest.raises(EDXMLValidationError, match='Empty object values are not valid'):
        DataType.base64().validate_object_value('')
    with pytest.raises(EDXMLValidationError, match='String is too long'):
        DataType.base64(length=15).validate_object_value('YW55IGNhcm5hbCBwbGVhcw==')


def test_validate_boolean():
    assert DataType.boolean().validate_object_value('true')
    assert DataType.boolean().validate_object_value('false')
    assert DataType.boolean().validate_object_value(True)
    assert DataType.boolean().validate_object_value(False)
    assert DataType.boolean().validate_object_value(1)
    assert DataType.boolean().validate_object_value(0)

    with pytest.raises(EDXMLValidationError, match='Invalid value string'):
        DataType.boolean().validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match='Invalid value'):
        DataType.boolean().validate_object_value(2)
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'float'"):
        DataType.boolean().validate_object_value(1.0)


def test_validate_uuid():
    assert DataType.uuid().validate_object_value('123e4567-e89b-12d3-a456-426614174000')

    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.uuid().validate_object_value(True)
    with pytest.raises(EDXMLValidationError, match="Invalid value string"):
        DataType.uuid().validate_object_value('123e4567-e89b-12d3-426614174000')


def test_validate_enum():
    assert DataType.enum('apples', 'oranges').validate_object_value('apples')
    assert DataType.enum('apples', 'oranges').validate_object_value('oranges')

    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.enum('apples', 'oranges').validate_object_value(True)
    with pytest.raises(EDXMLValidationError, match="Invalid value string"):
        DataType.enum('apples', 'oranges').validate_object_value('bananas')


def test_validate_file():
    assert DataType.file().validate_object_value('some/file.txt')

    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.file().validate_object_value(True)


def test_validate_sequence():
    assert DataType.sequence().validate_object_value(1)
    assert DataType.sequence().validate_object_value('1')

    with pytest.raises(EDXMLValidationError, match="cannot be negative"):
        DataType.sequence().validate_object_value(-1)
    with pytest.raises(EDXMLValidationError, match="Invalid value string"):
        DataType.sequence().validate_object_value('foo')
    with pytest.raises(EDXMLValidationError, match="cannot be used to store values of type 'bool'"):
        DataType.sequence().validate_object_value(True)
