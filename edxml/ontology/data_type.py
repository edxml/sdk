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

import base64
import codecs
import decimal
import re

from decimal import Decimal

from datetime import datetime

from IPy import IP
from dateutil.parser import parse
from lxml import etree
from lxml.builder import ElementMaker
from edxml.error import EDXMLEventValidationError, EDXMLOntologyValidationError


class DataType(object):
    """
    Class representing an EDXML data type. Instances of this class
    can be cast to strings, which yields the EDXML data-type attribute.
    """

    # Expression used for matching string datatypes
    STRING_PATTERN = re.compile("^string:[0-9]+:(mc|lc|uc)(:[ru]+)?$")
    # Expression used for matching base64 datatypes
    BASE64_PATTERN = re.compile("^base64:[0-9]+$")
    # Expression used for matching uri datatypes
    URI_PATTERN = re.compile("^uri:.$")
    # Expression used for matching uuid datatypes
    UUID_PATTERN = re.compile(
        r"^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$")
    # Expression used for matching valid EDXML datetime values
    DATETIME_PATTERN = r'(([2-9][0-9]{3})|(1(([6-9]\d{2})|(5((9\d)|(8[3-9]))))))-\d{2}-\d{2}T(([01]\d)|(2[0-3])).{13}Z'

    FAMILY_DATETIME = 'datetime'
    FAMILY_SEQUENCE = 'sequence'
    FAMILY_NUMBER = 'number'
    FAMILY_HEX = 'hex'
    FAMILY_UUID = 'uuid'
    FAMILY_BOOLEAN = 'boolean'
    FAMILY_STRING = 'string'
    FAMILY_BASE64 = 'base64'
    FAMILY_URI = 'uri'
    FAMILY_ENUM = 'enum'
    FAMILY_GEO = 'geo'
    FAMILY_IP = 'ip'
    FAMILY_FILE = 'file'

    def __init__(self, data_type):

        self.type = data_type

    def __str__(self):
        return self.type

    @classmethod
    def datetime(cls):
        """

        Create a datetime DataType instance.

        Returns:
          DataType:
        """

        return cls('datetime')

    @classmethod
    def sequence(cls):
        """

        Create a sequence DataType instance.

        Returns:
          DataType:
        """

        return cls('sequence')

    @classmethod
    def boolean(cls):
        """

        Create a boolean value DataType instance.

        Returns:
          edxml.ontology.DataType:
        """

        return cls('boolean')

    @classmethod
    def tiny_int(cls, signed=True):
        """

        Create an 8-bit tinyint DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:tinyint%s' % (':signed' if signed else ''))

    @classmethod
    def small_int(cls, signed=True):
        """

        Create a 16-bit smallint DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:smallint%s' % (':signed' if signed else ''))

    @classmethod
    def medium_int(cls, signed=True):
        """

        Create a 24-bit mediumint DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:mediumint%s' % (':signed' if signed else ''))

    @classmethod
    def int(cls, signed=True):
        """

        Create a 32-bit int DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:int%s' % (':signed' if signed else ''))

    @classmethod
    def big_int(cls, signed=True):
        """

        Create a 64-bit bigint DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:bigint%s' % (':signed' if signed else ''))

    @classmethod
    def float(cls, signed=True):
        """

        Create a 32-bit float DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:float%s' % (':signed' if signed else ''))

    @classmethod
    def double(cls, signed=True):
        """

        Create a 64-bit double DataType instance.

        Args:
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:double%s' % (':signed' if signed else ''))

    @classmethod
    def decimal(cls, total_digits, fractional_digits, signed=True):
        """

        Create a decimal DataType instance.

        Args:
          total_digits (int): Total number of digits
          fractional_digits (int): Number of digits after the decimal point
          signed (bool): Create signed or unsigned number

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:decimal:%d:%d%s' % (total_digits, fractional_digits, (':signed' if signed else '')))

    @classmethod
    def currency(cls):
        """

        Create a currency DataType instance.

        Returns:
          edxml.ontology.DataType:
        """
        return cls('number:currency')

    @classmethod
    def string(cls, length=0, lower_case=True, upper_case=True, require_unicode=True, reverse_storage=False):
        """

        Create a string DataType instance.

        Args:
          length (int): Max number of characters (zero = unlimited)
          lower_case (bool): Allow lower case characters
          upper_case (bool): Allow upper case characters
          require_unicode (bool): String may contain UTF-8 characters
          reverse_storage (bool): Hint storing the string in reverse character order

        Returns:
          edxml.ontology.DataType:
        """
        flags = 'u' if require_unicode else ''
        flags += 'r' if reverse_storage else ''

        if lower_case:
            if upper_case:
                case = 'mc'
            else:
                case = 'lc'
        else:
            if upper_case:
                case = 'uc'
            else:
                raise ValueError(
                    "String values cannot be prevented from containing both upper case and lower case characters."
                )

        return cls('string:%d:%s%s' % (length, case, ':%s' % flags if flags else ''))

    @classmethod
    def base64(cls, length=0):
        """

        Create a base64 DataType instance.

        Args:
          length (int): Max number of bytes (zero = unlimited)

        Returns:
          DataType:
        """

        return cls('base64:%d' % length)

    @classmethod
    def enum(cls, *choices):
        """

        Create an enumeration DataType instance.

        Args:
          *choices (str): Possible string values

        Returns:
          edxml.ontology.DataType:
        """
        return cls('enum:%s' % ':'.join(choices))

    @classmethod
    def uri(cls, path_separator='/'):
        """

        Create an URI DataType instance.

        Args:
          path_separator (str): URI path separator

        Returns:
          edxml.ontology.DataType:
        """
        return cls('uri:%s' % path_separator)

    @classmethod
    def hex(cls, length, separator=None, group_size=None):
        """

        Create a hexadecimal number DataType instance.

        Args:
          length (int): Number of hex digits
          separator (str): Separator character
          group_size (int): Number of hex digits per group

        Returns:
          edxml.ontology.DataType:
        """
        return cls('hex:%d%s' % (length, ':%d:%s' % (group_size, separator) if separator and group_size else ''))

    @classmethod
    def uuid(cls):
        """

        Create a uuid DataType instance.

        Returns:
          DataType:
        """

        return cls('uuid')

    @classmethod
    def geo_point(cls):
        """

        Create a geographical location DataType instance.

        Returns:
          edxml.ontology.DataType:
        """
        return cls('geo:point')

    @classmethod
    def file(cls):
        """

        Create a file DataType instance.

        Returns:
          edxml.ontology.DataType:
        """
        return cls('file')

    @classmethod
    def ip_v4(cls):
        """

        Create an IPv4 DataType instance

        Returns:
          edxml.ontology.DataType:
        """
        return cls('ip:v4')

    @classmethod
    def ip_v6(cls):
        """

        Create an IPv6 DataType instance

        Returns:
          edxml.ontology.DataType:
        """
        return cls('ip:v6')

    def get(self):
        """

        Returns the EDXML data-type attribute. Calling this
        method is equivalent to casting to a string.

        Returns:
          str:
        """
        return self.type

    def get_family(self):
        """

        Returns the data type family.

        Returns:
          str:
        """
        return self.type.split(':')[0]

    def get_split(self):
        """

        Returns the EDXML data type attribute, split on
        the colon (':'), yielding a list containing the
        individual parts of the data type.

        Returns:
          List[str]:
        """
        return self.type.split(':')

    def is_numerical(self):
        """

        Returns True if the data type is of data type
        family 'number'. Returns False for all other data types.

        Returns:
          boolean:
        """

        return self.type.split(':')[0] == 'number'

    def is_datetime(self):
        """

        Returns True if the data type is 'datetime'. Returns
        False for all other data types.

        Returns:
          boolean:
        """

        return self.type.split(':')[0] == 'datetime'

    def is_valid_upgrade_of(self, other):
        """

        Checks if the data type is a valid upgrade of
        another data type.

        Args:
            other (DataType): The other data type

        Returns:
            bool:
        """
        if self.get_family() != 'enum':
            return False
        if other.get_family() != 'enum':
            return False
        if len(self.get_split()) <= len(other.get_split()):
            return False

        previous_length = len(other.type)

        if self.type[:previous_length] != other.type[:previous_length]:
            return False

        return True

    def _generate_schema_datetime(self):
        # We use a a restricted dateTime data type,
        # which does not allow dates before 1583 or the 24th
        # hour. Also, it requires an explicit UTC timezone
        # and 6 decimal fractional seconds.
        e = ElementMaker()
        return e.data(
            e.param(self.DATETIME_PATTERN, name='pattern'),
            type='dateTime'
        )

    def _generate_schema_sequence(self):
        return ElementMaker().data(type='unsignedLong')

    def _generate_schema_number(self):
        e = ElementMaker()
        split_data_type = self.type.split(':')

        if split_data_type[1] in ('tinyint', 'smallint', 'mediumint', 'int', 'bigint'):
            if split_data_type[1] == 'tinyint':
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(type='byte')
                else:
                    element = e.data(type='unsignedByte')

            elif split_data_type[1] == 'smallint':
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(type='short')
                else:
                    element = e.data(type='unsignedShort')

            elif split_data_type[1] == 'mediumint':
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(
                        e.param(str(-(2 ** 23) + 1), name='minInclusive'),
                        e.param(str(+(2 ** 23) - 1), name='maxInclusive'),
                        type='int'
                    )
                else:
                    element = e.data(
                        e.param(str((2 ** 24) - 1), name='maxInclusive'),
                        type='unsignedInt'
                    )

            elif split_data_type[1] == 'int':
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(type='int')
                else:
                    element = e.data(type='unsignedInt')

            else:
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(type='long')
                else:
                    element = e.data(type='unsignedLong')

            if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                # Assure that values are not zero padded, zero is
                # not signed and no plus sign is present
                etree.SubElement(element, 'param',
                                 name='pattern').text = r'(-?[1-9]\d*)|0'
            else:
                # Assure that values are not zero padded and no
                # plus sign is present
                etree.SubElement(element, 'param', name='pattern').text = r'([1-9]\d*)|0'

            return element

        elif split_data_type[1] in ('float', 'double'):
            if split_data_type[1] == 'float':
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(type='float')
                else:
                    element = e.data(e.param(str(0), name='minInclusive'), type='float')
            else:
                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    element = e.data(type='double')
                else:
                    element = e.data(e.param(str(0), name='minInclusive'), type='double')

            # Assure that special values like NaN, +INF and -INF are not considered valid.
            etree.SubElement(element, 'param', name='pattern').text = r'[+-]?\d+(\.\d+)?(E[+-]\d+)?'

            return element

        elif split_data_type[1] == 'decimal':
            digits, fractional = split_data_type[2:4]
            element = e.data(
                e.param(digits, name='totalDigits'),
                e.param(fractional, name='fractionDigits'),
                type='decimal'
            )

            if len(split_data_type) < 5:
                etree.SubElement(element, 'param', name='minInclusive').text = str(0)
                # Assure that integer part is not zero padded, fractional part
                # is padded and no plus sign is present
                etree.SubElement(element, 'param', name='pattern').text = \
                    r'([1-9][0-9]*\..{%d})|(0\..{%d})' % (int(fractional), int(fractional))
            else:
                # Assure that integer part is not zero padded, fractional part
                # is padded, zero is unsigned and no plus sign is present
                etree.SubElement(element, 'param', name='pattern').text = \
                    r'(-?[1-9][0-9]*\..{%d})|(-?0\.\d*[1-9]\d*)|(0\.0{%d})' % (int(fractional), int(fractional))

            return element

        elif split_data_type[1] == 'currency':
            element = e.data(
                e.param('19', name='totalDigits'),
                e.param('4', name='fractionDigits'),
                type='decimal'
            )

            # Assure that integer part is not zero padded, fractional part
            # is padded, zero is unsigned and no plus sign is present
            etree.SubElement(element, 'param', name='pattern').text = \
                r'(-?[1-9][0-9]*\..{4})|(-?0\.\d*[1-9]\d*)|(0\.0{4})'

            return element

        else:
            raise TypeError('Unknown data type: ' + split_data_type[0])

    def _generate_schema_uri(self):
        # Note that anyURI XML data type allows anything, we could
        # also have used a string data type here.
        return ElementMaker().data(type='anyURI')

    def _generate_schema_hex(self):
        e = ElementMaker()
        split_data_type = self.type.split(':')

        digits = int(split_data_type[1]) * 2
        if len(split_data_type) <= 2:
            # Simple hexadecimal value. Note that we restrict
            # the character space to lowercase characters only.
            return e.data(e.param(r'[a-f\d]{%d}' % digits, name='pattern'), type='hexBinary')

        group_length = int(split_data_type[2]) * 2
        group_separator = split_data_type[3]
        num_groups = digits / group_length

        if len(group_separator) == 0:
            if len(split_data_type) == 5:
                # This happens if the colon ':' is used as separator
                group_separator = ':'

        if num_groups == 0:
            # zero groups means empty string. Empty strings
            # are not valid in EDXML.
            raise TypeError('Invalid hex data type (group size is zero): ' + self.type)

        if num_groups == 1:
            # We have just one digit group, so no separators are used.
            return e.data(e.param(r'[a-f\d]{%d}' % group_length, name='pattern'), type='string')

        return e.data(
            e.param(
                r'[a-f\d]{%d}(%s[a-f\d]{%d}){%d}' %
                (group_length, group_separator, group_length, num_groups - 1),
                name='pattern'
            ), type='string'
        )

    def _generate_schema_uuid(self):
        e = ElementMaker()
        # Note that we restrict the character space to lowercase characters only.
        return e.data(
            e.param(r'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}', name='pattern'),
            type='string'
        )

    def _generate_schema_string(self, regexp):
        e = ElementMaker()
        split_data_type = self.type.split(':')

        length = int(split_data_type[1])
        is_unicode = len(split_data_type) > 3 and 'u' in split_data_type[3]
        case = split_data_type[2]

        element = e.data(type='string')
        etree.SubElement(element, 'param', name='minLength').text = '1'

        if length > 0:
            etree.SubElement(element, 'param', name='maxLength').text = str(length)

        if is_unicode:
            if case == 'lc':
                etree.SubElement(element, 'param', name='pattern').text = r'[\s\S-[\p{Lu}]]*'
            elif case == 'uc':
                etree.SubElement(element, 'param', name='pattern').text = r'[\s\S-[\p{Ll}]]*'
        else:
            if case == 'mc':
                etree.SubElement(element, 'param', name='pattern').text = r'[\p{IsBasicLatin}\p{IsLatin-1Supplement}]*'
            elif case == 'lc':
                etree.SubElement(
                    element, 'param', name='pattern'
                ).text = r'[\p{IsBasicLatin}\p{IsLatin-1Supplement}-[\p{Lu}]]*'
            else:
                etree.SubElement(
                    element, 'param', name='pattern'
                ).text = r'[\p{IsBasicLatin}\p{IsLatin-1Supplement}-[\p{Ll}]]*'

        if regexp is not None:
            etree.SubElement(element, 'param', name='pattern').text = regexp

        return element

    def _generate_schema_base64(self):
        e = ElementMaker()
        split_data_type = self.type.split(':')

        # Because we do not allow whitespace in base64 values,
        # we use a pattern to restrict the data type.
        return e.data(
            e.param('1', name='minLength'),
            e.param(split_data_type[1], name='maxLength'),
            e.param(r'\S*', name='pattern'),
            type='base64Binary'
        )

    def _generate_schema_boolean(self):
        e = ElementMaker()

        return e.choice(
            e.value('true', type='string'),
            e.value('false', type='string'),
        )

    def _generate_schema_enum(self):
        e = ElementMaker()
        split_data_type = self.type.split(':')

        element = e.choice()
        for allowed_value in split_data_type[1:]:
            element.append(e.value(allowed_value))

        return element

    def _generate_schema_ip(self):
        split_data_type = self.type.split(':')
        e = ElementMaker()

        if split_data_type[1] == 'v4':
            # There is no data type in RelaxNG for IPv4 addresses,
            # so we use a pattern restriction. The regular expression
            # checks for four octets containing a integer number in
            # range [0,255].
            return e.data(
                e.param(
                    '((1?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]).){3}(1?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])',
                    name='pattern'
                ), type='string'
            )
        else:
            return e.data(
                e.param(
                    r'[a-f\d]{4}(:[a-f\d]{4}){7}',
                    name='pattern'
                ), type='string'
            )

    def _generate_schema_file(self):
        # Note that anyURI XML data type allows anything, we could
        # also have used a string data type here.
        return ElementMaker().data(type='anyURI')

    def _generate_schema_geo(self):
        split_data_type = self.type.split(':')

        if split_data_type[1] != 'point':
            raise TypeError('Unknown EDXML data type: "%s"' % self.type)

        e = ElementMaker()

        # Comma separated latitude and longitude. We check for
        # these components to be in their valid ranges. For latitude
        # this is [-90, +90]. For longitude [-180, +180].
        return e.data(
            e.param(
                (
                    r'('
                    r'-?(([1-8][0-9]|[0-9])(\.\d{6})),'
                    r'(-?(([1-9][0-9]|1[0-7]\d|[0-9])\.\d{6})|(180\.0{6}))'
                    r')|(-?90.000000,0.000000)'
                ),
                name='pattern'), type='string'
        )

    def generate_relaxng(self, regexp):

        data_type_family = self.get_family()

        if data_type_family == 'datetime':
            return self._generate_schema_datetime()
        elif data_type_family == 'sequence':
            return self._generate_schema_sequence()
        elif data_type_family == 'number':
            return self._generate_schema_number()
        elif data_type_family == 'uri':
            return self._generate_schema_uri()
        elif data_type_family == 'hex':
            return self._generate_schema_hex()
        elif data_type_family == 'uuid':
            return self._generate_schema_uuid()
        elif data_type_family == 'string':
            return self._generate_schema_string(regexp)
        elif data_type_family == 'base64':
            return self._generate_schema_base64()
        elif data_type_family == 'boolean':
            return self._generate_schema_boolean()
        elif data_type_family == 'enum':
            return self._generate_schema_enum()
        elif data_type_family == 'ip':
            return self._generate_schema_ip()
        elif data_type_family == 'file':
            return self._generate_schema_file()
        elif data_type_family == 'geo':
            return self._generate_schema_geo()
        else:
            raise TypeError('Unknown EDXML data type: "%s"' % self.type)

    def _normalize_datetime(self, values):
        normalized = set()
        for value in values:
            if isinstance(value, datetime):
                normalized.add(self.format_utc_datetime(value))
            elif isinstance(value, str):
                try:
                    normalized.add(self.format_utc_datetime(parse(value)))
                except Exception:
                    raise EDXMLEventValidationError('Invalid datetime string: %s' % value)
        return normalized

    def _normalize_number(self, values):
        split_data_type = self.type.split(':')

        if split_data_type[1] == 'decimal':
            decimal_precision = split_data_type[3]
            try:
                return {('%.' + decimal_precision + 'f') % Decimal(value) for value in values}
            except (TypeError, decimal.InvalidOperation):
                raise EDXMLEventValidationError(
                    'Invalid decimal value in list: "%s"' % '","'.join([repr(value) for value in values])
                )
        elif split_data_type[1] == 'currency':
            try:
                return {'%.4f' % Decimal(value) for value in values}
            except (TypeError, decimal.InvalidOperation):
                raise EDXMLEventValidationError(
                    'Invalid currency value in list: "%s"' % '","'.join([repr(value) for value in values])
                )
        elif split_data_type[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint']:
            try:
                return {'%d' % int(value) for value in values}
            except (TypeError, ValueError):
                raise EDXMLEventValidationError(
                    'Invalid integer value in list: "%s"' % '","'.join([repr(value) for value in values])
                )
        elif split_data_type[1] in ['float', 'double']:
            try:
                normalized = set()
                for value in values:
                    value = '%E' % float(value)
                    if 'e' not in value.lower():
                        # This happens for special values
                        # like NaN or INF
                        raise ValueError
                    normalized.add('%E' % float(value))
            except ValueError:
                raise EDXMLEventValidationError(
                    'Invalid floating point value in list: "%s"' % '","'.join([repr(value) for value in values])
                )
            else:
                return normalized

    def _normalize_hex(self, values):
        try:
            return {str(value.lower()) for value in values}
        except AttributeError:
            raise EDXMLEventValidationError(
                'Invalid hexadecimal value in list: "%s"' % '","'.join([repr(value) for value in values])
            )

    def _normalize_uri(self, values):
        try:
            return {value + '' for value in values}
        except TypeError:
            raise EDXMLEventValidationError(
                'Invalid URI value in list: "%s"' % '","'.join([repr(value) for value in values])
            )

    def _normalize_ip(self, values):
        split_data_type = self.type.split(':')
        normalized = set()
        for value in values:
            if not isinstance(value, IP):
                try:
                    value = IP(value)
                    if split_data_type[1] == 'v4' and value.version() != 4:
                        raise ValueError
                    if split_data_type[1] == 'v6' and value.version() != 6:
                        raise ValueError
                except (ValueError, TypeError):
                    raise EDXMLEventValidationError(
                        'Invalid IP%s address in list: "%s"' %
                        (split_data_type[1], '","'.join([repr(value) for value in values]))
                    )
            normalized.add(value.strFullsize())
        return normalized

    def _normalize_geo(self, values):
        split_data_type = self.type.split(':')
        if split_data_type[1] == 'point':
            try:
                return {'%.6f,%.6f' % tuple(float(coord) for coord in value.split(',')) for value in values}
            except (ValueError, TypeError):
                raise EDXMLEventValidationError(
                    'Invalid geo:point value in list: "%s"' % '","'.join([repr(value) for value in values])
                )

    def _normalize_string(self, values):
        split_data_type = self.type.split(':')

        max_len = int(split_data_type[1])

        if max_len > 0:
            if [value for value in values if len(value) > max_len]:
                # At least one value is too long and we can not
                # normalize it without loosing data.
                raise EDXMLEventValidationError(
                    'Invalid string value in list: "%s"' % '","'.join([repr(value) for value in values])
                )

        if split_data_type[2] == 'lc':
            return {str(value).lower() for value in values}
        elif split_data_type[2] == 'uc':
            return {str(value).upper() for value in values}
        else:
            return {str(value) for value in values}

    def _normalize_base64(self, values):
        normalized = set()
        try:
            for value in values:
                value = value.encode('utf-8')
                value += (b'=' * (len(value) % 4))
                base64.decodebytes(value)
                normalized.add(value.decode('utf-8'))
        except (AttributeError, ValueError):
            raise EDXMLEventValidationError(
                'Invalid base64 value in list: "%s"' % '","'.join([repr(value) for value in values])
            )
        return normalized

    def _normalize_boolean(self, values):
        return {'true' if value in (True, 'true', 'True', 1) else 'false' for value in values}

    def normalize_objects(self, values):
        """Normalize values to valid EDXML object value strings

        Converts each of the provided values into valid string
        representations for the data type. It takes an iterable
        as input and returns a set of normalized strings.

        The object values must be appropriate for the data type.
        For example, numerical data types require values that
        can be cast into a number, string data types require
        values that can be cast to a string. Values of datetime
        data type may be datetime instances or any string that
        dateutil can parse. When inappropriate values are
        encountered, an EDXMLEventValidationError will be raised.

        Args:
          values (Iterable[Any]): The input object values

        Raises:
          EDXMLEventValidationError

        Returns:
          Set[str]. The normalized object values
        """

        split_data_type = self.type.split(':')

        if split_data_type[0] == 'datetime':
            return self._normalize_datetime(values)
        elif split_data_type[0] == 'number':
            return self._normalize_number(values)
        elif split_data_type[0] == 'hex':
            return self._normalize_hex(values)
        elif split_data_type[0] == 'uri':
            return self._normalize_uri(values)
        elif split_data_type[0] == 'ip':
            return self._normalize_ip(values)
        elif split_data_type[0] == 'geo':
            return self._normalize_geo(values)
        elif split_data_type[0] == 'string':
            return self._normalize_string(values)
        elif split_data_type[0] == 'base64':
            return self._normalize_base64(values)
        elif split_data_type[0] == 'boolean':
            return self._normalize_boolean(values)
        else:
            return {str(value) for value in values}

    def _validate_value_datetime(self, value):
        if isinstance(value, str):
            if not re.match(r'^' + self.DATETIME_PATTERN + '$', value):
                raise EDXMLEventValidationError("Invalid value string for data type %s: '%s'." % (self.type, value))
        elif not isinstance(value, datetime):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

    def _validate_value_sequence(self, value):
        if isinstance(value, str):
            try:
                int(value)
            except (TypeError, ValueError):
                raise EDXMLEventValidationError("Invalid value string for data type %s: '%s'." % (self.type, value))
            value = int(value)

        if isinstance(value, bool) or not isinstance(value, int):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

        if value < 0:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Sequence values cannot be negative" % (self.type, value)
            )

    def _validate_value_number(self, value):
        split_data_type = self.type.split(':')

        if split_data_type[1] == 'decimal':
            if isinstance(value, str):
                try:
                    Decimal(value)
                except decimal.InvalidOperation:
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. " % (self.type, value)
                    )
                try:
                    [integral, fractional] = value.split('.')
                except ValueError:
                    # No decimal dot found.
                    [integral, fractional] = value, ''

                if len(fractional) != int(split_data_type[3]):
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. "
                        "Must have %s fractional digits." %
                        (self.type, value, split_data_type[3])
                    )
                if int(integral) == 0 and int(fractional) == 0 and integral[:1] in ('+', '-'):
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. "
                        "Zero must not have any sign." %
                        (self.type, value)
                    )
                if len(integral) > 1 and integral[0] == '0':
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. "
                        "Zero padding of the integral part is not allowed." %
                        (self.type, value)
                    )
                value = Decimal(value)

            if isinstance(value, bool) or not (
                    isinstance(value, int) or isinstance(value, float) or isinstance(value, Decimal)
            ):
                raise EDXMLEventValidationError(
                    "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
                )

            if len(split_data_type) < 5:
                # Decimal is unsigned.
                if value < 0:
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. Value is negative." % (self.type, value)
                    )
        elif split_data_type[1] == 'currency':
            if isinstance(value, str):
                try:
                    Decimal(value)
                except decimal.InvalidOperation:
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. " % (self.type, value)
                    )
                try:
                    [integral, fractional] = value.split('.')
                except ValueError:
                    # No decimal dot found.
                    [integral, fractional] = value, ''

                if len(fractional) != 4:
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. "
                        "Must have four fractional digits." %
                        (self.type, value)
                    )
                if int(integral) == 0 and int(fractional) == 0 and integral[:1] in ('+', '-'):
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. "
                        "Zero must not have any sign." %
                        (self.type, value)
                    )
                if len(integral) > 1 and integral[0] == '0':
                    raise EDXMLEventValidationError(
                        "Invalid value string for data type %s: '%s'. "
                        "Zero padding of the integral part is not allowed." %
                        (self.type, value)
                    )
                value = Decimal(value)

            if isinstance(value, bool) or not (
                    isinstance(value, int) or isinstance(value, float) or isinstance(value, Decimal)
            ):
                raise EDXMLEventValidationError(
                    "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
                )
        elif split_data_type[1] in ['float', 'double']:
            if isinstance(value, str):
                try:
                    float(value)
                    if 'e' not in ('%E' % float(value)).lower():
                        raise ValueError
                except ValueError:
                    raise EDXMLEventValidationError("Invalid value string for data type %s: '%s'." % (self.type, value))
                value = float(value)

            if isinstance(value, bool) or not (isinstance(value, int) or isinstance(value, float)):
                raise EDXMLEventValidationError(
                    "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
                )

            if len(split_data_type) < 3:
                # number is unsigned.
                if value < 0:
                    raise EDXMLEventValidationError("Unsigned %s value is negative: '%s'." % (self.type, value))

        else:  # int, bigint, tinyint, ...
            if isinstance(value, str):
                try:
                    int(value)
                except (TypeError, ValueError):
                    raise EDXMLEventValidationError("Invalid value string for data type %s: '%s'." % (self.type, value))
                value = int(value)

            if isinstance(value, bool) or not isinstance(value, int):
                raise EDXMLEventValidationError(
                    "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
                )

            if len(split_data_type) < 3:
                # number is unsigned.
                if value < 0:
                    raise EDXMLEventValidationError("Unsigned integer value is negative: '%s'." % value)

    def _validate_value_hex(self, value):
        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

        split_data_type = self.type.split(':')

        if value.lower() != value:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Must be all lowercase." % (self.type, value)
            )

        if len(split_data_type) > 2:
            # TODO: Also check for empty groups, or more generically: group size.
            hex_separator = split_data_type[3]
            if len(hex_separator) == 0 and len(split_data_type) == 5:
                hex_separator = ':'
            value = ''.join(c for c in str(value) if c != hex_separator)

        if len(value) / 2 != int(split_data_type[1]):
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Incorrect length." % (self.type, value)
            )

        try:
            codecs.decode(value.encode(), 'hex')
        except (TypeError, ValueError):
            raise EDXMLEventValidationError("Invalid value string for data type %s: '%s'." % (self.type, value))

    def _validate_value_uuid(self, value):
        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )
        if not re.match(self.UUID_PATTERN, value):
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Must be all lowercase." % (self.type, value)
            )

    def _validate_value_geo(self, value):
        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

        split_geo_point = value.split(',')

        try:
            geo_lat = float(split_geo_point[0])
            geo_lon = float(split_geo_point[1])
        except (TypeError, ValueError, IndexError):
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'." % (self.type, value)
            )

        try:
            if len(split_geo_point[0].split('.')) != 2:
                raise ValueError
            if len(split_geo_point[1].split('.')) != 2:
                raise ValueError
        except ValueError:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Missing decimal dot." % (self.type, value)
            )
        if len(split_geo_point[0].split('.')[1]) != 6:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Missing latitude decimals." % (self.type, value)
            )
        if len(split_geo_point[1].split('.')[1]) != 6:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Missing longitude decimals." % (self.type, value)
            )
        if geo_lat < -90 or geo_lat > 90:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Latitude not within range [-90,90]." % (self.type, value)
            )
        if geo_lon < -180 or geo_lon > 180:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Longitude not within range [-180,180]." %
                (self.type, value)
            )
        if split_geo_point[0].startswith('+'):
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Latitude has a leading '+' sign." % (self.type, value)
            )
        if split_geo_point[1].startswith('+'):
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'. Longitude has a leading '+' sign." % (self.type, value)
            )

    def _validate_value_string(self, value):

        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

        split_data_type = self.type.split(':')

        # Check length of object value
        max_string_length = int(split_data_type[1])
        if max_string_length > 0:
            if len(value) > max_string_length:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'. String is too long." % (self.type, value)
                )

        if split_data_type[2] == 'lc':
            if value.lower() != value:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'. String must be all lowercase." % (self.type, value)
                )
        elif split_data_type[2] == 'uc':
            if value.upper() != value:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'. String must be all uppercase." % (self.type, value)
                )

        # Check character set of object value
        if len(split_data_type) < 4 or 'u' not in split_data_type[3]:
            # String should only contain latin1 characters.
            try:
                str(value).encode('latin1')
            except (LookupError, ValueError):
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'. String contains non-latin1 characters." %
                    (self.type, value)
                )

    def _validate_value_uri(self, value):
        # URI values can be any string, we do not validate the strings.
        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

    def _validate_value_base64(self, value):
        split_data_type = self.type.split(':')

        try:
            decoded = base64.decodebytes(value.encode())
        except (AttributeError, ValueError):
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'." % (self.type, value)
            )

        max_string_length = int(split_data_type[1])

        if max_string_length > 0:
            if len(decoded) > max_string_length:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'. String is too long." % (self.type, value)
                )

    def _validate_value_file(self, value):
        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )
        # file values can be any string, nothing else to validate.

    def _validate_value_ip(self, value):
        split_data_type = self.type.split(':')
        if isinstance(value, str):
            try:
                ip = IP(value)
            except ValueError:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'." % (self.type, value)
                )
            if ip.strFullsize() != value:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'. IP addresses must not be shortened or zero padded." %
                    (self.type, value)
                )
        elif isinstance(value, IP):
            ip = value
        else:
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

        try:
            if split_data_type[1] == 'v4' and ip.version() != 4:
                raise ValueError
            if split_data_type[1] == 'v6' and ip.version() != 6:
                raise ValueError
        except ValueError:
            raise EDXMLEventValidationError(
                "Invalid value string for data type %s: '%s'." % (self.type, value)
            )

    def _validate_value_boolean(self, value):
        if isinstance(value, str):
            if value not in ['true', 'false']:
                raise EDXMLEventValidationError(
                    "Invalid value string for data type %s: '%s'." % (self.type, value)
                )
        elif isinstance(value, bool) or isinstance(value, int):
            if value not in [True, False, 0, 1]:
                raise EDXMLEventValidationError(
                    "Invalid value for data type %s: '%s'." % (self.type, value)
                )
        else:
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )

    def _validate_value_enum(self, value):
        if not isinstance(value, str):
            raise EDXMLEventValidationError(
                "Data type %s cannot be used to store values of type '%s'." % (self.type, type(value).__name__)
            )
        split_data_type = self.type.split(':')
        if value not in split_data_type[1:]:
            raise EDXMLEventValidationError("Invalid value string for data type %s: '%s'" % (self.type, value))

    def validate_object_value(self, value):
        """

        Validates the provided object value against
        the data type, raising an EDXMLValidationException
        when the value is invalid.
        The value may be a native type like an integer or
        a boolean. The value may also be a unicode encoded
        string, as it would appear in EDXML data.

        Args:
          value: Object value
        Raises:
          EDXMLEventValidationError
        Returns:
           edxml.ontology.DataType:
        """
        if value in ['', None]:
            raise EDXMLEventValidationError(
                "Value of %s object is empty. Empty object values are not valid and must be omitted." % self.type
            )

        data_type_family = self.get_family()

        if data_type_family == 'datetime':
            self._validate_value_datetime(value)
        elif data_type_family == 'sequence':
            self._validate_value_sequence(value)
        elif data_type_family == 'number':
            self._validate_value_number(value)
        elif data_type_family == 'hex':
            self._validate_value_hex(value)
        elif data_type_family == 'uuid':
            self._validate_value_uuid(value)
        elif data_type_family == 'geo':
            self._validate_value_geo(value)
        elif data_type_family == 'string':
            self._validate_value_string(value)
        elif data_type_family == 'uri':
            self._validate_value_uri(value)
        elif data_type_family == 'base64':
            self._validate_value_base64(value)
        elif data_type_family == 'file':
            self._validate_value_file(value)
        elif data_type_family == 'ip':
            self._validate_value_ip(value)
        elif data_type_family == 'boolean':
            self._validate_value_boolean(value)
        elif data_type_family == 'enum':
            self._validate_value_enum(value)

        return self

    def _validate_decimal(self):
        split_data_type = self.type.split(':')

        if len(split_data_type) < 4:
            raise EDXMLOntologyValidationError('Data type "%s" is not a valid EDXML data type.' % self.type)

        try:
            decimal_num_digits = int(split_data_type[2])
        except ValueError:
            raise EDXMLOntologyValidationError(
                "Total number of digits specified in data type %s is invalid." % self.type
            )
        if decimal_num_digits < 1:
            raise EDXMLOntologyValidationError(
                "Total number of digits specified in data type %s must be positive." % self.type
            )
        if decimal_num_digits > 38:
            raise EDXMLOntologyValidationError(
                "Total number of digits specified in data type %s must not exceed 38." % self.type
            )

        try:
            decimal_num_decimals = int(split_data_type[3])
        except ValueError:
            raise EDXMLOntologyValidationError("Number of decimals specified in data type %s is invalid." % self.type)
        if decimal_num_digits <= decimal_num_decimals:
            raise EDXMLOntologyValidationError(
                "Total number of digits specified in data type %s must be greater than "
                "the number of decimals." % self.type
            )

        if len(split_data_type) > 4:
            if len(split_data_type) == 5:
                if split_data_type[4] == 'signed':
                    return
        else:
            return

    def _validate_number(self):
        split_data_type = self.type.split(':')
        if split_data_type[1] in ('tinyint', 'smallint', 'mediumint', 'int', 'bigint', 'float', 'double'):
            if len(split_data_type) == 3:
                if split_data_type[2] == 'signed':
                    return
            elif len(split_data_type) == 2:
                return
        elif split_data_type[1:] == ['currency']:
            return
        elif split_data_type[1] == 'decimal':
            self._validate_decimal()
            return

        raise EDXMLOntologyValidationError('Data type "%s" is not a valid EDXML data type.' % self.type)

    def _validate_hex(self):
        split_data_type = self.type.split(':')
        try:
            hex_length = int(split_data_type[1])
        except (KeyError, ValueError):
            raise EDXMLOntologyValidationError("Hex datatype does not specify a valid length: " + self.type)
        if hex_length == 0:
            raise EDXMLOntologyValidationError("Length of hex datatype must be greater than zero: " + self.type)
        if len(split_data_type) > 2:
            try:
                digit_group_length = int(split_data_type[2])
            except ValueError:
                pass
            else:
                if digit_group_length == 0:
                    raise EDXMLOntologyValidationError(
                        "Group length in hex datatype must be greater than zero: " + self.type
                    )
                if hex_length % digit_group_length != 0:
                    raise EDXMLOntologyValidationError(
                        "Length of hex datatype is not a multiple of separator distance: " + self.type
                    )
                if len(split_data_type[3]) == 0:
                    if len(split_data_type) == 5:
                        # This happens if the colon ':' is used as separator
                        return
                else:
                    return
        else:
            return

        raise EDXMLOntologyValidationError('Data type "%s" is not a valid EDXML data type.' % self.type)

    def validate(self):
        """

        Validates the data type definition, raising an
        EDXMLValidationException when the definition is
        not valid.

        Raises:
          EDXMLOntologyValidationError
        Returns:
           edxml.ontology.DataType:
        """

        # Some data type families have just one member and
        # do not require any further validation.
        if self.type in ('datetime', 'sequence', 'file', 'boolean', 'uuid'):
            return self

        split_data_type = self.type.split(':')

        if split_data_type[0] == 'enum':
            if len(split_data_type) > 1:
                return self
        elif split_data_type[0] == 'geo':
            if len(split_data_type) == 2:
                if split_data_type[1] == 'point':
                    return self
        elif split_data_type[0] == 'ip':
            if len(split_data_type) == 2:
                if split_data_type[1] in ('v4', 'v6'):
                    return self
        elif split_data_type[0] == 'number':
            self._validate_number()
            return self
        elif split_data_type[0] == 'hex':
            self._validate_hex()
            return self
        elif split_data_type[0] == 'string':
            if re.match(self.STRING_PATTERN, self.type):
                return self
        elif split_data_type[0] == 'base64':
            if re.match(self.BASE64_PATTERN, self.type):
                return self
        elif split_data_type[0] == 'uri':
            if re.match(self.URI_PATTERN, self.type):
                return self

        raise EDXMLOntologyValidationError('Data type "%s" is not a valid EDXML data type.' % self.type)

    @classmethod
    def format_utc_datetime(cls, date_time):
        """

        Formats specified dateTime object into a valid
        EDXML datetime string.

        Notes:

          The datetime object must have its time zone
          set to UTC.

        Args:
          date_time (datetime.datetime): datetime object

        Returns:
          str: EDXML datetime string
        """
        try:
            return date_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            # Dates before year 1900 are not supported by strftime.
            date_time = date_time.isoformat()
            # The isoformat method yields a string formatted like
            #
            # YYYY-MM-DDTHH:MM:SS.mmmmmm
            #
            # unless the fractional part is zero. In that case, the
            # fractional part is omitted, yielding invalid EDXML. Also,
            # the UTC timezone is represented as '+00:00' rather than 'Z'.
            if date_time[19] != '.':
                return date_time[:19] + '.000000Z'
            else:
                return date_time[:26] + 'Z'
