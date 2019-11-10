# -*- coding: utf-8 -*-
import urllib
from urlparse import urlsplit, urlunsplit

import re

from decimal import Decimal

from datetime import datetime
from dateutil.parser import parse
from lxml import etree
from lxml.builder import ElementMaker
from edxml.error import EDXMLValidationError


class DataType(object):
    """
    Class representing an EDXML data type. Instances of this class
    can be cast to strings, which yields the EDXML data-type attribute.
    """

    # Expression used for matching SHA1 hashlinks
    HASHLINK_PATTERN = re.compile("^[0-9a-zA-Z]{40}$")
    # Expression used for matching string datatypes
    STRING_PATTERN = re.compile("^string:[0-9]+:((cs)|(ci))(:[ru]+)?$")
    # Expression used for matching base64 datatypes
    BASE64_PATTERN = re.compile("^base64:[0-9]+$")
    # Expression used for matching uri datatypes
    URI_PATTERN = re.compile("^uri:.$")
    # Expression used for matching uuid datatypes
    UUID_PATTERN = re.compile(
        r"^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$")

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
    FAMILY_HASHLINK = 'hashlink'

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
    def string(cls, length=0, case_sensitive=True, require_unicode=True, reverse_storage=False):
        """

        Create a string DataType instance.

        Args:
          length (int): Max number of characters (zero = unlimited)
          case_sensitive (bool): Treat strings as case insensitive
          require_unicode (bool): String may contain UTF-8 characters
          reverse_storage (bool): Hint storing the string in reverse character order

        Returns:
          edxml.ontology.DataType:
        """
        flags = 'u' if require_unicode else ''
        flags += 'r' if reverse_storage else ''

        return cls('string:%d:%s%s' % (length, 'cs' if case_sensitive else 'ci', ':%s' % flags if flags else ''))

    @classmethod
    def base64(cls, length=0):
        """

        Create a base64 DataType instance.

        Args:
          length (int): Max number of bytes (zero = unlimited)

        Returns:
          DataType:
        """

        return cls('base64')

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
    def hashlink(cls):
        """

        Create a hashlink DataType instance.

        Returns:
          edxml.ontology.DataType:
        """
        return cls('hashlink')

    @classmethod
    def ip_v4(cls):
        """

        Create an IPv4 DataType instance

        Returns:
          edxml.ontology.DataType:
        """
        return cls('ip')

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

    def generate_relaxng(self, regexp):

        e = ElementMaker()
        split_data_type = self.type.split(':')

        if split_data_type[0] == 'datetime':
            # We use a a restricted dateTime data type,
            # which does not allow dates before 1583 or the 24th
            # hour. Also, it requires an explicit UTC timezone
            # and 6 decimal fractional seconds.
            element = e.data(
                e.param(
                    r'(([2-9][0-9]{3})|(1(([6-9]\d{2})|(5((9\d)|(8[3-9]))))))-\d{2}-\d{2}T(([01]\d)|(2[0-3])).{13}Z',
                    name='pattern'),
                type='dateTime'
            )

        elif split_data_type[0] == 'sequence':
            element = e.data(type='unsignedLong')

        elif split_data_type[0] == 'number':
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
                        element = e.data(type='short')
                    else:
                        element = e.data(type='unsignedShort')

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
                    etree.SubElement(element, 'param',
                                     name='pattern').text = r'([1-9]\d*)|0'

            elif split_data_type[1] in ('float', 'double'):
                if split_data_type[1] == 'float':
                    if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                        element = e.data(type='float')
                    else:
                        element = e.data(
                            e.param(str(0), name='minInclusive'), type='float')
                else:
                    if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                        element = e.data(type='double')
                    else:
                        element = e.data(
                            e.param(str(0), name='minInclusive'), type='double')

                if len(split_data_type) > 2 and split_data_type[2] == 'signed':
                    # Assure that values are in 1.234567E+001 format, no leading
                    # plus sign is present and zero is not signed.
                    etree.SubElement(
                        element, 'param', name='pattern').text = r'(-?[^0]\.\d{6}E[+-]\d{3})|0\.000000E[+]000'
                else:
                    # Assure that values are in 1.234567E+001 format and not leading
                    # plus sign is present.
                    etree.SubElement(
                        element, 'param', name='pattern').text = r'([^0]\.\d{6}E[+-]\d{3})|0\.000000E[+]000'

            elif split_data_type[1] == 'decimal':
                digits, fractional = split_data_type[2:4]
                element = e.data(
                    e.param(digits, name='totalDigits'),
                    e.param(fractional, name='fractionDigits'),
                    type='decimal'
                )

                if len(split_data_type) < 5:
                    etree.SubElement(element, 'param',
                                     name='minInclusive').text = str(0)
                    # Assure that integer part is not zero padded, fractional part
                    # is padded and no plus sign is present
                    etree.SubElement(element, 'param', name='pattern').text = \
                        r'([^+0][^+]*\..{%d})|(0\..{%d})' % (
                            int(fractional), int(fractional))
                else:
                    # Assure that integer part is not zero padded, fractional part
                    # is padded, zero is unsigned and no plus sign is present
                    etree.SubElement(element, 'param', name='pattern').text = \
                        r'(-?[^+0-][^+]*\..{%d})|(-?0\.\d*[1-9]\d*)|(0\.0{%d})' % \
                        (int(fractional), int(fractional))
            else:
                raise TypeError

        elif split_data_type[0] == 'uri':
            # Note that anyURI XML data type allows virtually anything,
            # we need to use a regular expression to restrict it to the
            # set of characters allowed in an URI.
            element = e.data(type='anyURI')

        elif split_data_type[0] == 'hex':
            digits = int(split_data_type[1])
            if len(split_data_type) > 2:
                # We have separated digit groups.
                group_length = int(split_data_type[2])
                group_separator = split_data_type[3]
                num_groups = digits / group_length
                if len(group_separator) == 0:
                    if len(split_data_type) == 5:
                        # This happens if the colon ':' is used as separator
                        group_separator = ':'
                if num_groups > 0:
                    if num_groups > 1:
                        element = e.data(
                            e.param(
                                r'[a-f\d]{%d}(%s[a-f\d]{%d}){%d}' % (group_length,
                                                                     group_separator, group_length, num_groups - 1),
                                name='pattern'
                            ), type='string'
                        )
                    else:
                        element = e.data(
                            e.param(
                                r'[a-f\d]{%d}' % group_length,
                                name='pattern'
                            ), type='string'
                        )
                else:
                    # zero groups means empty string.
                    element = e.value(type='string')
            else:
                # Simple hexadecimal value. Note that we restrict
                # the character space to lowercase characters.
                element = e.data(
                    e.param(r'[a-f\d]{%d}' % digits, name='pattern'), type='hexBinary')

        elif split_data_type[0] == 'uuid':
            # Note that we restrict the character space to lowercase characters.
            element = e.data(e.param(
                r'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}', name='pattern'), type='string')

        elif split_data_type[0] == 'string':
            length = int(split_data_type[1])
            is_unicode = len(split_data_type) > 3 and 'u' in split_data_type[3]
            is_case_sensitive = split_data_type[2] == 'cs'
            element = e.data(type='string')
            etree.SubElement(element, 'param', name='minLength').text = '1'
            if length > 0:
                etree.SubElement(element, 'param',
                                 name='maxLength').text = str(length)
            if not is_unicode:
                if is_case_sensitive:
                    etree.SubElement(
                        element, 'param', name='pattern').text = r'[\p{IsBasicLatin}\p{IsLatin-1Supplement}]*'
                else:
                    etree.SubElement(
                        element, 'param', name='pattern').text = r'[\p{IsBasicLatin}\p{IsLatin-1Supplement}-[\p{Lu}]]*'
            if regexp is not None:
                etree.SubElement(element, 'param', name='pattern').text = regexp

        elif split_data_type[0] == 'base64':
            # Because we do not allow whitespace in base64 values,
            # we use a pattern to restrict the data type.
            element = e.data(
                e.param(1, name='minLength'),
                e.param(split_data_type[1], name='maxLength'),
                e.param(r'\S*', name='pattern'),
                type='base64Binary'
            )

        elif split_data_type[0] == 'boolean':
            # Because we do not allow the value strings '0' and '1'
            # while the RelaxNG data type does, we need to add
            # these two values as exceptions.
            element = e.data(
                e('except',
                  e.choice(
                      e.value('0', type='string'),
                      e.value('1', type='string'),
                  )
                  ), type='boolean'
            )

        elif split_data_type[0] == 'enum':
            element = e.choice()
            for allowedValue in split_data_type[1:]:
                element.append(e.value(allowedValue))

        elif split_data_type[0] == 'ip':
            # There is no data type in RelaxNG for IP addresses,
            # so we use a pattern restriction. The regular expression
            # checks for four octets containing a integer number in
            # range [0,255].
            element = e.data(
                e.param(
                    '((1?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]).){3}(1?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])',
                    name='pattern'
                ), type='string'
            )

        elif split_data_type[0] == 'hashlink':
            # Hashlink is a hex encoded 20-byte SHA1
            element = e.data(e.param('20', name='length'), type='hexBinary')

        elif split_data_type[0] == 'geo' and split_data_type[1] == 'point':
            # Comma separated latitude and longitude. We check for
            # these components to be in their valid ranges. For latitude
            # this is [-90, +90]. For longitude [-180, +180].
            element = e.data(
                e.param(
                    (
                        r'-?((([1-8][0-9]|[0-9])(\.\d+)?)|(90(\.0{0,6})?)),'
                        r'-?((([1-9][0-9]|1[0-7]\d|[0-9])(\.\d{0,6})?)|(180(\.0{0,6})?))'
                    ),
                    name='pattern'), type='string'
            )

        else:
            raise TypeError('Unknown EDXML data type: "%s"' % self.type)

        return element

    def normalize_objects(self, values):
        """Normalize values to valid EDXML object value strings

        Converts each of the provided values into unicode strings
        that are valid string representations for the data type.
        It takes an iterable as input and returns a set of
        normalized unicode strings.

        The object values must be appropriate for the data type.
        For example, numerical data types require values that
        can be cast into a number, string data types require
        values that can be cast to a string. Values of datetime
        data type may be datetime instances or any string that
        dateutil can parse. When inappropriate values are
        encountered, an EDXMLValidationError will be raised.

        Args:
          values (List[Any]): The input object values

        Raises:
          EDXMLValidationError

        Returns:
          Set[unicode]. The normalized object values
        """

        split_data_type = self.type.split(':')

        if split_data_type[0] == 'datetime':
            normalized = set()
            for value in values:
                if isinstance(value, datetime):
                    normalized.add(self.format_utc_datetime(value))
                elif type(value) in (str, unicode):
                    try:
                        normalized.add(self.format_utc_datetime(parse(value)))
                    except Exception:
                        raise EDXMLValidationError(
                            'Invalid datetime string: %s' % value)
            return normalized
        elif split_data_type[0] == 'number':
            if split_data_type[1] == 'decimal':
                decimal_precision = split_data_type[3]
                try:
                    return {unicode('%.' + decimal_precision + 'f') % Decimal(value) for value in values}
                except TypeError:
                    raise EDXMLValidationError(
                        'Invalid decimal value in list: "%s"' % '","'.join(
                            [repr(value) for value in values])
                    )
            elif split_data_type[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint']:
                try:
                    return {u'%d' % int(value) for value in values}
                except (TypeError, ValueError):
                    raise EDXMLValidationError(
                        'Invalid integer value in list: "%s"' % '","'.join(
                            [repr(value) for value in values])
                    )
            elif split_data_type[1] in ['float', 'double']:
                try:
                    normalized = set()
                    for value in values:
                        value = u'%.6E' % float(value)
                        mantissa, exponent = value.split('E')
                        if mantissa in ('0.000000', '-0.000000'):
                            normalized.add('0.000000E+000')
                        else:
                            normalized.add('%sE%+04d' % (mantissa, int(exponent)))
                except ValueError:
                    raise EDXMLValidationError(
                        'Invalid floating point value in list: "%s"' % '","'.join(
                            [repr(value) for value in values])
                    )
                else:
                    return normalized

        elif split_data_type[0] == 'hex':
            try:
                return {unicode(value.lower()) for value in values}
            except AttributeError:
                raise EDXMLValidationError(
                    'Invalid hexadecimal value in list: "%s"' % '","'.join(
                        [repr(value) for value in values])
                )

        elif split_data_type[0] == 'uri':
            path_separator = ':' if split_data_type[1] == '' else split_data_type[1]
            normalized = set()
            for value in values:
                # Note that we cannot safely re-quote URIs in case there
                # is a problem with quoting of special characters. For example,
                # the path may contain both literal slashes and escaped ones. The
                # server may interpret the literal slashes as path separators but not
                # the quoted ones. When unquoting and requoting, this difference is
                # lost. So we will not attempt to do that here. We will only apply
                # quoting in case there are illegal characters in the URI and no percent
                # encoding is present, which implies that the URI has not been quoted at all.
                try:
                    scheme, netloc, path, qs, anchor = urlsplit(value)
                except ValueError:
                    continue

                # Note that a path may start with a slash irrespective of the actual path separator.
                path = urllib.quote(path, '/' + path_separator)
                # Quote the query part.
                qs = urllib.quote_plus(qs, ':&=')
                # Reconstruct normalized value.
                normalized.add(urlunsplit(
                    (scheme, netloc, path, qs, anchor))
                )
            return normalized

        elif split_data_type[0] == 'ip':
            try:
                return {u'%d.%d.%d.%d' % tuple(int(octet) for octet in value.split('.')) for value in values}
            except (ValueError, TypeError):
                raise EDXMLValidationError(
                    'Invalid IPv4 address in list: "%s"' % '","'.join(
                        [repr(value) for value in values])
                )
        elif split_data_type[0] == 'geo':
            if split_data_type[1] == 'point':
                try:
                    return {u'%.6f,%.6f' % tuple(float(coord) for coord in value.split(',')) for value in values}
                except (ValueError, TypeError):
                    raise EDXMLValidationError(
                        'Invalid geo:point value in list: "%s"' % '","'.join(
                            [repr(value) for value in values])
                    )
        elif split_data_type[0] == 'string':
            try:
                if split_data_type[2] == 'ci':
                    return {unicode(value.lower()) for value in values}
                else:
                    return {unicode(value) for value in values}
            except AttributeError:
                raise EDXMLValidationError(
                    'Invalid string value in list: "%s"' % '","'.join(
                        [repr(value) for value in values])
                )
        elif split_data_type[0] == 'base64':
            try:
                {value.decode('base64') for value in values}
            except (AttributeError, ValueError):
                raise EDXMLValidationError(
                    'Invalid byte string value in list: "%s"' % '","'.join(
                        [repr(value) for value in values])
                )
            return values
        elif split_data_type[0] == 'boolean':
            return {'true' if value in (True, 'true', 'True', 1) else 'false' for value in values}
        else:
            try:
                return {unicode(value) for value in values}
            except AttributeError:
                raise EDXMLValidationError(
                    'Invalid string value in list: "%s"' % '","'.join(
                        [repr(value) for value in values])
                )

    def validate_object_value(self, value):
        """

        Validates the provided object value against
        the data type, raising an EDXMLValidationException
        when the value is invalid.

        Args:
          value (unicode): Object value
        Raises:
          EDXMLValidationError
        Returns:
           edxml.ontology.DataType:
        """
        if type(value) not in (str, unicode):
            raise EDXMLValidationError(
                'Value for data type %s is not a string: %s' % (self.type, repr(value)))

        split_data_type = self.type.split(':')

        if split_data_type[0] == 'datetime':
            if not re.match(
                r'^(([2-9][0-9]{3})|(1(([6-9]\d{2})|(5((9\d)|(8[3-9]))))))-\d{2}-\d{2}T(([01]\d)|(2[0-3])).{13}Z$',
                    value):
                raise EDXMLValidationError(
                    "Invalid value for data type %s: '%s'." % (self.type, value))
        elif split_data_type[0] == 'sequence':
            try:
                int(value)
            except (TypeError, ValueError):
                raise EDXMLValidationError(
                    "Invalid sequence value '%s'." % value)
        elif split_data_type[0] == 'number':
            if split_data_type[1] == 'decimal':
                if len(split_data_type) < 5:
                    # Decimal is unsigned.
                    if Decimal(value) < 0:
                        raise EDXMLValidationError(
                            "Unsigned decimal value '%s' is negative." % value)
            elif split_data_type[1] == 'float' or split_data_type[1] == 'double':
                try:
                    value = float(value)
                except ValueError:
                    raise EDXMLValidationError(
                        "Invalid floating point number '%s'." % value)
                if len(split_data_type) < 3:
                    # number is unsigned.
                    if value < 0:
                        raise EDXMLValidationError(
                            "Unsigned floating point value is negative: '%s'." % value)
            else:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    raise EDXMLValidationError("Invalid number '%s'." % value)
                if len(split_data_type) < 3:
                    # number is unsigned.
                    if value < 0:
                        raise EDXMLValidationError(
                            "Unsigned integer value is negative: '%s'." % value)
        elif split_data_type[0] == 'hex':
            if value.lower() != value:
                raise EDXMLValidationError(
                    "string of data type %s must be all lowercase: %s" % (self.type, value))
            if len(split_data_type) > 2:
                # TODO: Also check for empty groups, or more generically: group size.
                hex_separator = split_data_type[3]
                if len(hex_separator) == 0 and len(split_data_type) == 5:
                    hex_separator = ':'
                value = ''.join(c for c in str(value) if c != hex_separator)
            try:
                value.decode("hex")
            except (TypeError, ValueError):
                raise EDXMLValidationError("Invalid hexadecimal value '%s'." % value)
        elif split_data_type[0] == 'uuid':
            if not re.match(self.UUID_PATTERN, value):
                raise EDXMLValidationError("Invalid uuid value: '%s'" % value)
        elif split_data_type[0] == 'geo':
            if split_data_type[1] == 'point':
                # This is the only option at the moment.
                split_geo_point = value.split(',')
                if len(split_geo_point) != 2:
                    raise EDXMLValidationError(
                        "The geo:point value '%s' is not formatted correctly." % value)
                try:
                    geo_lat = float(split_geo_point[0])
                    geo_lon = float(split_geo_point[1])
                except (TypeError, ValueError):
                    raise EDXMLValidationError(
                        "The geo:point value '%s' is not formatted correctly." % value)
                if geo_lat < -90 or geo_lat > 90:
                    raise EDXMLValidationError(
                        "The geo:point value '%s' contains a latitude that is not within range [-90,90]." % value)
                if geo_lon < -180 or geo_lon > 180:
                    raise EDXMLValidationError(
                        "The geo:point value '%s' contains a longitude that is not within range [-180,180]." % value)
            else:
                raise EDXMLValidationError(
                    "Invalid geo data type: '%s'" % value)
        elif split_data_type[0] == 'string':

            # Check length of object value
            if value == '':
                raise EDXMLValidationError(
                    "Value of %s object is empty." % self.type)
            max_string_length = int(split_data_type[1])
            if max_string_length > 0:
                if len(value) > max_string_length:
                    raise EDXMLValidationError(
                        "string too long for data type %s: '%s'" % (self.type, value))

            if split_data_type[2] == 'ci':
                if value.lower() != value:
                    raise EDXMLValidationError(
                        "string of data type %s must be all lowercase: %s" % (self.type, value))

            # Check character set of object value
            if len(split_data_type) < 4 or 'u' not in split_data_type[3]:
                # String should only contain latin1 characters.
                try:
                    unicode(value).encode('latin1')
                except (LookupError, ValueError):
                    raise EDXMLValidationError(
                        "string of data type %s contains unicode characters: %s" % (self.type, value))
        elif split_data_type[0] == 'uri':
            # URI values can be any string, nothing to validate.
            pass
        elif split_data_type[0] == 'base64':

            # Check length of object value
            if value == '':
                raise EDXMLValidationError(
                    "Value of %s object is empty." % self.type)
            try:
                decoded = value.decode(encoding='base64')
            except AttributeError:
                raise EDXMLValidationError(
                    "Invalid base64 encoded string: '%s'" % value)

            max_string_length = int(split_data_type[1])

            if max_string_length > 0:
                if len(decoded) > max_string_length:
                    raise EDXMLValidationError(
                        "base64 encoded string too long for data type %s: '%s'" % (self.type, value))
        elif split_data_type[0] == 'hashlink':
            if not re.match(self.HASHLINK_PATTERN, value):
                raise EDXMLValidationError("Invalid hashlink: '%s'" % value)
        elif split_data_type[0] == 'ip':
            split_ip = value.split('.')
            if len(split_ip) != 4:
                raise EDXMLValidationError(
                    "Invalid IPv4 address: '%s'" % value)
            for split_ip_part in split_ip:
                try:
                    if not 0 <= int(split_ip_part) <= 255:
                        raise EDXMLValidationError(
                            "Invalid IPv4 address: '%s'" % value)
                except (TypeError, ValueError):
                    raise EDXMLValidationError(
                        "Invalid IPv4 address: '%s'" % value)
        elif split_data_type[0] == 'boolean':
            object_string = value.lower()
            if object_string not in ['true', 'false']:
                raise EDXMLValidationError("Invalid boolean: '%s'" % value)
        elif split_data_type[0] == 'enum':
            if value not in split_data_type[1:]:
                raise EDXMLValidationError(
                    "Invalid value for data type %s: '%s'" % (self.type, value))
        else:
            raise EDXMLValidationError("Invalid data type: '%s'" % self.type)

        return self

    def validate(self):
        """

        Validates the data type definition, raising an
        EDXMLValidationException when the definition is
        not valid.

        Raises:
          EDXMLValidationError
        Returns:
           edxml.ontology.DataType:
        """
        split_data_type = self.type.split(':')

        if split_data_type[0] == 'enum':
            if len(split_data_type) > 1:
                return self
        elif split_data_type[0] == 'datetime':
            if len(split_data_type) == 1:
                return self
        elif split_data_type[0] == 'sequence':
            if len(split_data_type) == 1:
                return self
        elif split_data_type[0] == 'ip':
            if len(split_data_type) == 1:
                return self
        elif split_data_type[0] == 'hashlink':
            if len(split_data_type) == 1:
                return self
        elif split_data_type[0] == 'boolean':
            if len(split_data_type) == 1:
                return self
        elif split_data_type[0] == 'geo':
            if len(split_data_type) == 2:
                if split_data_type[1] == 'point':
                    return self
        elif split_data_type[0] == 'number':
            if len(split_data_type) >= 2:
                if split_data_type[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint', 'float', 'double']:
                    if len(split_data_type) == 3:
                        if split_data_type[2] == 'signed':
                            return self
                    else:
                        return self
                elif split_data_type[1] == 'decimal':
                    if len(split_data_type) >= 4:
                        try:
                            int(split_data_type[2])
                            int(split_data_type[3])
                        except ValueError:
                            pass
                        else:
                            if int(split_data_type[3]) > int(split_data_type[2]):
                                raise EDXMLValidationError(
                                    "Invalid Decimal: " + self.type)
                            if len(split_data_type) > 4:
                                if len(split_data_type) == 5:
                                    if split_data_type[4] == 'signed':
                                        return self
                            else:
                                return self
        elif split_data_type[0] == 'hex':
            try:
                hex_length = int(split_data_type[1])
            except (KeyError, ValueError):
                raise EDXMLValidationError(
                    "Hex datatype does not specify a valid length: " + self.type)
            if hex_length == 0:
                raise EDXMLValidationError(
                    "Length of hex datatype must be greater than zero: " + self.type)
            if len(split_data_type) > 2:
                try:
                    digit_group_length = int(split_data_type[2])
                except ValueError:
                    pass
                else:
                    if digit_group_length == 0:
                        raise EDXMLValidationError(
                            "Group length in hex datatype must be greater than zero: " + self.type)
                    if hex_length % digit_group_length != 0:
                        raise EDXMLValidationError(
                            "Length of hex datatype is not a multiple of separator distance: " + self.type)
                    if len(split_data_type[3]) == 0:
                        if len(split_data_type) == 5:
                            # This happens if the colon ':' is used as separator
                            return self
                    else:
                        return self
            else:
                return self
        elif split_data_type[0] == 'uuid':
            if len(split_data_type) == 1:
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

        raise EDXMLValidationError(
            'Data type "%s" is not a valid EDXML data type.' % self.type)

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
