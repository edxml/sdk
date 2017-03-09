# -*- coding: utf-8 -*-
from decimal import Decimal

import re
from lxml import etree
from lxml.builder import ElementMaker

from edxml.EDXMLBase import EDXMLValidationError


class DataType(object):
  """
  Class representing an EDXML data type. Instances of this class
  can be cast to strings, which yields the EDXML data-type attribute.
  """

  # Expression used for matching SHA1 hashlinks
  HASHLINK_PATTERN = re.compile("^[0-9a-zA-Z]{40}$")
  # Expression used for matching string datatypes
  STRING_PATTERN = re.compile("string:[0-9]+:((cs)|(ci))(:[ru]+)?")
  # Expression used for matching binstring datatypes
  BINSTRING_PATTERN = re.compile("binstring:[0-9]+(:r)?")

  def __init__(self, data_type):

    self.type = data_type

  def __str__(self):
    return self.type

  @classmethod
  def DateTime(cls):
    """

    Create a datetime DataType instance.

    Returns:
      DataType:
    """

    return cls('datetime')

  @classmethod
  def Boolean(cls):
    """

    Create a boolean value DataType instance.

    Returns:
      edxml.ontology.DataType:
    """

    return cls('boolean')

  @classmethod
  def TinyInt(cls, Signed = True):
    """

    Create an 8-bit tinyint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:tinyint%s' % (':signed' if Signed else ''))

  @classmethod
  def SmallInt(cls, Signed = True):
    """

    Create a 16-bit smallint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:smallint%s' % (':signed' if Signed else ''))

  @classmethod
  def MediumInt(cls, Signed = True):
    """

    Create a 24-bit mediumint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:mediumint%s' % (':signed' if Signed else ''))

  @classmethod
  def Int(cls, Signed = True):
    """

    Create a 32-bit int DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:int%s' % (':signed' if Signed else ''))

  @classmethod
  def BigInt(cls, Signed = True):
    """

    Create a 64-bit bigint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:bigint%s' % (':signed' if Signed else ''))

  @classmethod
  def Float(cls, Signed = True):
    """

    Create a 32-bit float DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:float%s' % (':signed' if Signed else ''))

  @classmethod
  def Double(cls, Signed = True):
    """

    Create a 64-bit double DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:double%s' % (':signed' if Signed else ''))

  @classmethod
  def Decimal(cls, TotalDigits, FractionalDigits, Signed = True):
    """

    Create a decimal DataType instance.

    Args:
      TotalDigits (int): Total number of digits
      FractionalDigits (int): Number of digits after the decimal point
      Signed (bool): Create signed or unsigned number

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:decimal:%d:%d%s' % (TotalDigits, FractionalDigits, (':signed' if Signed else '')))

  @classmethod
  def String(cls, Length = 0, CaseSensitive = True, RequireUnicode = True, ReverseStorage = False):
    """

    Create a string DataType instance.

    Args:
      Length (int): Max number of characters (zero = unlimited)
      CaseSensitive (bool): Treat strings as case insensitive
      RequireUnicode (bool): String may contain UTF-8 characters
      ReverseStorage (bool): Hint storing the string in reverse character order

    Returns:
      edxml.ontology.DataType:
    """
    Flags = 'u' if RequireUnicode else ''
    Flags += 'r' if ReverseStorage else ''

    return cls('string:%d:%s%s' % (Length, 'cs' if CaseSensitive else 'ci', ':%s' % Flags if Flags else ''))

  @classmethod
  def Enum(cls, *Choices):
    """

    Create an enumeration DataType instance.

    Args:
      *Choices (str): Possible string values

    Returns:
      edxml.ontology.DataType:
    """
    return cls('enum:%s' % ':'.join(Choices))

  @classmethod
  def Hexadecimal(cls, Length, Separator=None, GroupSize=None):
    """

    Create a hexadecimal number DataType instance.

    Args:
      Length (int): Number of hex digits
      Separator (str): Separator character
      GroupSize (int): Number of hex digits per group

    Returns:
      edxml.ontology.DataType:
    """
    return cls('number:hex:%d%s' % (Length, ':%d:%s' % (GroupSize, Separator) if Separator and GroupSize else ''))

  @classmethod
  def GeoPoint(cls):
    """

    Create a geographical location DataType instance.

    Returns:
      edxml.ontology.DataType:
    """
    return cls('geo:point')

  @classmethod
  def Hashlink(cls):
    """

    Create a hashlink DataType instance.

    Returns:
      edxml.ontology.DataType:
    """
    return cls('hashlink')

  @classmethod
  def Ipv4(cls):
    """

    Create an IPv4 DataType instance

    Returns:
      edxml.ontology.DataType:
    """
    return cls('ip')

  def Get(self):
    """

    Returns the EDXML data-type attribute. Calling this
    method is equivalent to casting to a string.

    Returns:
      str:
    """
    return self.type

  def GetFamily(self):
    """

    Returns the data type family.

    Returns:
      str:
    """
    return self.type.split(':')[0]

  def GetSplit(self):
    """

    Returns the EDXML data type attribute, split on
    the colon (':'), yielding a list containing the
    individual parts of the data type.

    Returns:
      List[str]:
    """
    return self.type.split(':')[0]

  def IsNumerical(self):
    """

    Returns True if the data type is of data type
    family 'number', but not 'number:hex'. Returns
    False for all other data types.

    Returns:
      boolean:
    """

    splitDataType = self.type.split(':')
    if splitDataType[0] == 'number':
      # TODO: Remove this check for hex once it has
      # been removed from number family
      if splitDataType[1] != 'hex':
        return True
    elif splitDataType[0] == 'datetime':
      return True

    return False

  def GenerateRelaxNG(self, RegExp):

    e = ElementMaker()
    splitDataType = self.type.split(':')

    if splitDataType[0] == 'datetime':
      # We use a a restricted dateTime data type,
      # which does not allow dates before 1583 or the 24th
      # hour. Also, it requires an explicit UTC timezone
      # and 6 decimal fractional seconds.
      element = e.data(
          e.param('(([2-9][0-9]{3})|(1(([6-9]\d{2})|(5((9\d)|(8[3-9]))))))-\d{2}-\d{2}T(([01]\d)|(2[0-3])).{13}Z', name='pattern'),
          type='dateTime'
        )

    elif splitDataType[0] == 'number':
      if splitDataType[1] == 'tinyint':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='byte')
        else:
          element = e.data(type='unsignedByte')

      elif splitDataType[1] == 'smallint':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='short')
        else:
          element = e.data(type='unsignedShort')

      elif splitDataType[1] == 'mediumint':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='short')
        else:
          element = e.data(type='unsignedShort')

      elif splitDataType[1] == 'int':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='int')
        else:
          element = e.data(type='unsignedInt')

      elif splitDataType[1] == 'bigint':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='long')
        else:
          element = e.data(type='unsignedLong')

      elif splitDataType[1] == 'float':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='float')
        else:
          element = e.data(e.param(str(0), name='minInclusive'), type='float')

      elif splitDataType[1] == 'double':
        if len(splitDataType) > 2 and splitDataType[2] == 'signed':
          element = e.data(type='double')
        else:
          element = e.data(e.param(str(0), name='minInclusive'), type='double')

      elif splitDataType[1] == 'decimal':
        digits, fractional = splitDataType[2:4]
        element = e.data(
          e.param(digits, name='totalDigits'),
          e.param(fractional, name='fractionDigits'),
          type='decimal'
        )
        if len(splitDataType) < 4:
          etree.SubElement(element, 'param', name='minInclusive').text = str(0)

      elif splitDataType[1] == 'hex':
        digits = int(splitDataType[2])
        if len(splitDataType) > 3:
          # We have separated digit groups.
          groupLength = int(splitDataType[3])
          groupSeparator = splitDataType[4]
          numGroups = digits / groupLength
          if len(groupSeparator) == 0:
            if len(splitDataType) == 6:
              # This happens if the colon ':' is used as separator
              groupSeparator = ':'
          if numGroups > 0:
            if numGroups > 1:
              element = e.data(
                e.param(
                  '[A-Fa-f\d]{%d}(%s[A-Fa-f\d]{%d}){%d}' % (groupLength, groupSeparator, groupLength, numGroups - 1),
                  name='pattern'
                ), type='string'
              )
            else:
              element = e.data(
                e.param(
                  '[A-Fa-f\d]{%d}' % groupLength,
                  name='pattern'
                ), type='string'
              )
          else:
            # zero groups means empty string.
            element = e.value(type='string')
        else:
          # Simple hexadecimal value. Note that the length of
          # the RelaxNG datatype is given in bytes.
          element = e.data(e.param(str(int(digits) / 2), name='length'), type='hexBinary')
      else:
        raise TypeError

    elif splitDataType[0] == 'string':
      length = int(splitDataType[1])
      isUnicode = len(splitDataType) > 3 and 'u' in splitDataType[3]
      element = e.data(type='string')
      etree.SubElement(element, 'param', name='minLength').text = '1'
      if length > 0:
        etree.SubElement(element, 'param', name='maxLength').text = str(length)
      if not isUnicode:
        etree.SubElement(element, 'param', name='pattern').text = '[\p{IsBasicLatin}\p{IsLatin-1Supplement}]*'
      if RegExp != '[\s\S]*':
        etree.SubElement(element, 'param', name='pattern').text = RegExp

    elif splitDataType[0] == 'binstring':
      length = int(splitDataType[1])
      element = e.data(type='string')
      etree.SubElement(element, 'param', name='minLength').text = '1'
      if length > 0:
        etree.SubElement(element, 'param', name='maxLength').text = str(length)
      if RegExp != '[\s\S]*':
        etree.SubElement(element, 'param', name='pattern').text = RegExp

    elif splitDataType[0] == 'boolean':
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

    elif splitDataType[0] == 'enum':
      element = e.choice()
      for allowedValue in splitDataType[1:]:
        element.append(e.value(allowedValue))

    elif splitDataType[0] == 'ip':
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

    elif splitDataType[0] == 'hashlink':
      # Hashlink is a hex encoded 20-byte SHA1
      element = e.data(e.param('20', name='length'), type='hexBinary')

    elif splitDataType[0] == 'geo' and splitDataType[1] == 'point':
      # Comma separated latitude and longitude. We check for
      # these components to be in their valid ranges. For latitude
      # this is [-90, +90]. For longitude [-180, +180].
      element = e.data(
        e.param(
          (
            '-?((([1-8][0-9]|[0-9])(\.\d+)?)|(90(\.0{0,6})?)),'
            '-?((([1-9][0-9]|1[0-7]\d|[0-9])(\.\d{0,6})?)|(180(\.0{0,6})?))'
          ),
          name='pattern'), type='string'
      )

    else:
      raise TypeError('Unknown EDXML data type: "%s"' % self.type)

    return element

  def NormalizeObjects(self, values):
    """Normalize object values to unicode strings

    Prepares object values for computing sticky hashes, by
    applying the normalization rules as outlined in the EDXML
    specification. It takes a list of object values as input
    and returns a list of normalized unicode strings.

    The object values must be appropriate for the data type.
    For example, numerical data types require values that
    can be cast into a number, string data types require
    string values. When inappropriate values are encountered,
    an EDXMLValidationError will be raised.

    Args:
      values (List[Any]): The input object values

    Raises:
      EDXMLValidationError

    Returns:
      List[unicode]. The normalized object values
    """

    splitDataType = self.type.split(':')

    if splitDataType[0] == 'number':
      if splitDataType[1] == 'decimal':
        DecimalPrecision = splitDataType[3]
        try:
          return [unicode('%.' + DecimalPrecision + 'f') % Decimal(value) for value in values]
        except TypeError:
          raise EDXMLValidationError(
            'Invalid decimal value in list: "%s"' % '","'.join([repr(value) for value in values])
          )
      elif splitDataType[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint']:
        try:
          return [u'%d' % int(value) for value in values]
        except TypeError:
          raise EDXMLValidationError(
            'Invalid integer value in list: "%s"' % '","'.join([repr(value) for value in values])
          )
      elif splitDataType[1] in ['float', 'double']:
        try:
          return [u'%f' % float(value) for value in values]
        except TypeError:
          raise EDXMLValidationError(
            'Invalid floating point value in list: "%s"' % '","'.join([repr(value) for value in values])
          )
      else:
        # Must be hexadecimal
        try:
          return [unicode(value.lower()) for value in values]
        except AttributeError:
          raise EDXMLValidationError(
            'Invalid hexadecimal value in list: "%s"' % '","'.join([repr(value) for value in values])
          )
    elif splitDataType[0] == 'ip':
      try:
        return [u'%d.%d.%d.%d' % tuple(int(octet) for octet in value.split('.')) for value in values]
      except (ValueError, TypeError):
        raise EDXMLValidationError(
          'Invalid IPv4 address in list: "%s"' % '","'.join([repr(value) for value in values])
        )
    elif splitDataType[0] == 'geo':
      if splitDataType[1] == 'point':
        try:
          return [u'%.6f,%.6f' % tuple(float(Coordinate) for Coordinate in value.split(',')) for value in values]
        except (ValueError, TypeError):
          raise EDXMLValidationError(
            'Invalid geo:point value in list: "%s"' % '","'.join([repr(value) for value in values])
          )
    elif splitDataType[0] == 'string':
      try:
        if splitDataType[2] == 'ci':
          return [unicode(value.lower()) for value in values]
        else:
          return [unicode(value) for value in values]
      except AttributeError:
        raise EDXMLValidationError(
          'Invalid string value in list: "%s"' % '","'.join([repr(value) for value in values])
        )
    elif splitDataType[0] == 'boolean':
      try:
        return [unicode(value.lower() for value in values)]
      except AttributeError:
        raise EDXMLValidationError(
          'Invalid string value in list: "%s"' % '","'.join([repr(value) for value in values])
        )
    else:
      try:
        return [unicode(value) for value in values]
      except AttributeError:
        raise EDXMLValidationError(
          'Invalid string value in list: "%s"' % '","'.join([repr(value) for value in values])
        )

  def ValidateObjectValue(self, value):
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
      raise EDXMLValidationError('Value for data type %s is not a string: %s' % (self.type, repr(value)))

    splitDataType = self.type.split(':')

    if splitDataType[0] == 'datetime':
      if not re.match('^(([2-9][0-9]{3})|(1(([6-9]\d{2})|(5((9\d)|(8[3-9]))))))-\d{2}-\d{2}T(([01]\d)|(2[0-3])).{13}Z$', value):
        raise EDXMLValidationError("Invalid value for data type %s: '%s'." % (self.type, value))
    elif splitDataType[0] == 'number':
      if splitDataType[1] == 'decimal':
        if len(splitDataType) < 5:
          # Decimal is unsigned.
          if Decimal(value) < 0:
            raise EDXMLValidationError("Unsigned decimal value '%s' is negative." % value)
      elif splitDataType[1] == 'hex':
        if len(splitDataType) > 3:
          HexSeparator = splitDataType[4]
          if len(HexSeparator) == 0 and len(splitDataType) == 6:
            HexSeparator = ':'
          value = ''.join(c for c in str(value) if c != HexSeparator)
        try:
          value.decode("hex")
        except ValueError:
          raise EDXMLValidationError("Invalid hexadecimal value '%s'." % value)
      elif splitDataType[1] == 'float' or splitDataType[1] == 'double':
        try:
          float(value)
        except ValueError:
          raise EDXMLValidationError("Invalid floating point number '%s'." % value)
        if len(splitDataType) < 3:
          # number is unsigned.
          if value < 0:
            raise EDXMLValidationError("Unsigned floating point value is negative: '%s'." % value)
      else:
        try:
          int(value)
        except:
          raise EDXMLValidationError("Invalid number '%s'." % value)
        if len(splitDataType) < 3:
          # number is unsigned.
          if value < 0:
            raise EDXMLValidationError("Unsigned integer value is negative: '%s'." % value)
    elif splitDataType[0] == 'geo':
      if splitDataType[1] == 'point':
        # This is the only option at the moment.
        SplitGeoPoint = value.split(',')
        if len(SplitGeoPoint) != 2:
          raise EDXMLValidationError("The geo:point value '%s' is not formatted correctly." % value)
        try:
          GeoLat = float(SplitGeoPoint[0])
          GeoLon = float(SplitGeoPoint[1])
        except:
          raise EDXMLValidationError("The geo:point value '%s' is not formatted correctly." % value)
        if GeoLat < -90 or GeoLat > 90:
          raise EDXMLValidationError("The geo:point value '%s' contains a latitude that is not within range [-90,90]." % value)
        if GeoLon < -180 or GeoLon > 180:
          raise EDXMLValidationError("The geo:point value '%s' contains a longitude that is not within range [-180,180]." % value)
      else:
        raise EDXMLValidationError("Invalid geo data type: '%s'" % value)
    elif splitDataType[0] == 'string':

      # Check length of object value
      if value == '':
        raise EDXMLValidationError("Value of %s object is empty.")
      MaxStringLength = int(splitDataType[1])
      if MaxStringLength > 0:
        if len(value) > MaxStringLength:
          raise EDXMLValidationError("string too long for data type %s: '%s'" % (self.type, value))

      # Check character set of object value
      if len(splitDataType) < 4 or 'u' not in splitDataType[3]:
        # String should only contain latin1 characters.
        try:
          unicode(value).encode('latin1')
        except:
          raise EDXMLValidationError("string of data type %s contains unicode characters: %s" % (self.type, value))
    elif splitDataType[0] == 'binstring':
      if 0 < splitDataType[1] < len(value):
          raise EDXMLValidationError("string of data type %s too long: '%s'" % (self.type, value))
    elif splitDataType[0] == 'hashlink':
      if not re.match(self.HASHLINK_PATTERN, value):
        raise EDXMLValidationError("Invalid hashlink: '%s'" % value)
    elif splitDataType[0] == 'ip':
      SplitIp = value.split('.')
      if len(SplitIp) != 4:
        raise EDXMLValidationError("Invalid IPv4 address: '%s'" % value)
      for SplitIpPart in SplitIp:
        try:
          if not 0 <= int(SplitIpPart) <= 255:
            raise EDXMLValidationError("Invalid IPv4 address: '%s'" % value)
        except:
            raise EDXMLValidationError("Invalid IPv4 address: '%s'" % value)
    elif splitDataType[0] == 'boolean':
      ObjectString = value.lower()
      if ObjectString not in ['true', 'false']:
        raise EDXMLValidationError("Invalid boolean: '%s'" % value)
    elif splitDataType[0] == 'enum':
      if value not in splitDataType[1:]:
        raise EDXMLValidationError("Invalid value for data type %s: '%s'" % (self.type, value))
    else:
      raise EDXMLValidationError("Invalid data type: '%s'" % self.type)

    return self

  def Validate(self):
    """

    Validates the data type definition, raising an
    EDXMLValidationException when the definition is
    not valid.

    Raises:
      EDXMLValidationError
    Returns:
       edxml.ontology.DataType:
    """
    splitDataType = self.type.split(':')

    if splitDataType[0] == 'enum':
      if len(splitDataType) > 1:
        return self
    elif splitDataType[0] == 'datetime':
      if len(splitDataType) == 1:
        return self
    elif splitDataType[0] == 'ip':
      if len(splitDataType) == 1:
        return self
    elif splitDataType[0] == 'hashlink':
      if len(splitDataType) == 1:
        return self
    elif splitDataType[0] == 'boolean':
      if len(splitDataType) == 1:
        return self
    elif splitDataType[0] == 'geo':
      if len(splitDataType) == 2:
        if splitDataType[1] == 'point':
          return self
    elif splitDataType[0] == 'number':
      if len(splitDataType) >= 2:
        if splitDataType[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint', 'float', 'double']:
          if len(splitDataType) == 3:
            if splitDataType[2] == 'signed':
              return self
          else:
            return self
        elif splitDataType[1] == 'decimal':
          if len(splitDataType) >= 4:
            try:
              int(splitDataType[2])
              int(splitDataType[3])
            except ValueError:
              pass
            else:
              if int(splitDataType[3]) > int(splitDataType[2]):
                raise EDXMLValidationError("Invalid Decimal: " + self.type)
              if len(splitDataType) > 4:
                if len(splitDataType) == 5:
                  if splitDataType[4] == 'signed':
                    return self
              else:
                return self
        elif splitDataType[1] == 'hex':
          try:
            hexLength = int(splitDataType[2])
          except (KeyError, ValueError):
            raise EDXMLValidationError("Hex datatype does not specify a valid length: " + self.type)
          if hexLength == 0:
            raise EDXMLValidationError("Length of hex datatype must be greater than zero: " + self.type)
          if len(splitDataType) > 3:
            try:
              digitGroupLength = int(splitDataType[3])
            except ValueError:
              pass
            else:
              if digitGroupLength == 0:
                raise EDXMLValidationError("Group length in hex datatype must be greater than zero: " + self.type)
              if hexLength % digitGroupLength != 0:
                raise EDXMLValidationError("Length of hex datatype is not a multiple of separator distance: " + self.type)
              if len(splitDataType[4]) == 0:
                if len(splitDataType) == 6:
                  # This happens if the colon ':' is used as separator
                  return self
              else:
                return self
          else:
            return self
    elif splitDataType[0] == 'string':
      if re.match(self.STRING_PATTERN, self.type):
        return self
    elif splitDataType[0] == 'binstring':
      if re.match(self.BINSTRING_PATTERN, self.type):
        return self

    raise EDXMLValidationError('Data type "%s" is not a valid EDXML data type.' % self.type)

  @classmethod
  def FormatUtcDateTime(cls, dateTime):
    """

    Formats specified dateTime object into a valid
    EDXML datetime string.

    Notes:

      The datetime object must have its time zone
      set to UTC.

    Args:
      dateTime (datetime.datetime): datetime object

    Returns:
      str: EDXML datetime string
    """
    try:
      return dateTime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
      # Dates before year 1900 are not supported by strftime.
      dateTime = dateTime.isoformat()
      # The isoformat method yields a string formatted like
      #
      # YYYY-MM-DDTHH:MM:SS.mmmmmm
      #
      # unless the fractional part is zero. In that case, the
      # fractional part is omitted, yielding invalid EDXML. Also,
      # the UTC timezone is represented as '+00:00' rather than 'Z'.
      if dateTime[19] != '.':
        dateTime[19:] = '.000000Z'
      else:
        dateTime[25:].pad = 'Z'

      return dateTime
