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
  def Timestamp(cls):
    """

    Create a timestamp DataType instance.

    Returns:
      DataType:
    """

    return cls('timestamp')

  @classmethod
  def Boolean(cls):
    """

    Create a boolean value DataType instance.

    Returns:
      DataType:
    """

    return cls('boolean')

  @classmethod
  def TinyInt(cls, Signed = True):
    """

    Create an 8-bit tinyint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
    """
    return cls('number:tinyint%s' % (':signed' if Signed else ''))

  @classmethod
  def SmallInt(cls, Signed = True):
    """

    Create a 16-bit smallint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
    """
    return cls('number:smallint%s' % (':signed' if Signed else ''))

  @classmethod
  def MediumInt(cls, Signed = True):
    """

    Create a 24-bit mediumint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
    """
    return cls('number:mediumint%s' % (':signed' if Signed else ''))

  @classmethod
  def Int(cls, Signed = True):
    """

    Create a 32-bit int DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
    """
    return cls('number:int%s' % (':signed' if Signed else ''))

  @classmethod
  def BigInt(cls, Signed = True):
    """

    Create a 64-bit bigint DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
    """
    return cls('number:bigint%s' % (':signed' if Signed else ''))

  @classmethod
  def Float(cls, Signed = True):
    """

    Create a 32-bit float DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
    """
    return cls('number:float%s' % (':signed' if Signed else ''))

  @classmethod
  def Double(cls, Signed = True):
    """

    Create a 64-bit double DataType instance.

    Args:
      Signed (bool): Create signed or unsigned number

    Returns:
      DataType:
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
      DataType:
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
      DataType:
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
      DataType:
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
      DataType:
    """
    return cls('number:hex:%d%s' % (Length, ':%d:%s' % (GroupSize, Separator) if Separator and GroupSize else ''))

  @classmethod
  def GeoPoint(cls):
    """

    Create a geographical location DataType instance.

    Returns:
      DataType:
    """
    return cls('geo:point')

  @classmethod
  def Hashlink(cls):
    """

    Create a hashlink DataType instance.

    Returns:
      DataType:
    """
    return cls('hashlink')

  @classmethod
  def Ipv4(cls):
    """

    Create an IPv4 DataType instance

    Returns:
      DataType:
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

    Returns True if the data type is a timestamp or
    if the data type family is 'number', returns False
    for all other data types.

    Returns:
      boolean:
    """

    splitDataType = self.type.split(':')
    if splitDataType[0] == 'number':
      # TODO: Remove this check for hex once it has
      # been removed from number family
      if splitDataType[1] != 'hex':
        return True
    elif splitDataType[0] == 'timestamp':
      return True

    return False

  def GenerateRelaxNG(self, RegExp):

    e = ElementMaker()
    splitDataType = self.type.split(':')

    if splitDataType[0] == 'timestamp':
      element = e.data(
          e.param('20', name='totalDigits'),
          e.param('6', name='fractionDigits'),
          type='decimal'
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
      if length > 0:
        etree.SubElement(element, 'param', name='maxLength').text = str(length)
      if not isUnicode:
        etree.SubElement(element, 'param', name='pattern').text = '[\p{IsBasicLatin}\p{IsLatin-1Supplement}]*'
      if RegExp != '[\s\S]*':
        etree.SubElement(element, 'param', name='pattern').text = RegExp

    elif splitDataType[0] == 'binstring':
      length = int(splitDataType[1])
      element = e.data(type='string')
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

  def NormalizeObject(self, value):
    """Normalize an object value to a unicode string

    Prepares an object value for computing sticky hashes, by
    applying the normalization rules as outlined in the EDXML
    specification. It takes a string containing an object value
    as input and returns a normalized unicode string.

    Args:
      value (str, unicode): The input object value

    Returns:
      unicode. The normalized object value

    calls :func:`Error` when value is invalid.
    """

    splitDataType = self.type.split(':')

    if splitDataType[0] == 'timestamp':
      return u'%.6f' % Decimal(value)
    elif splitDataType[0] == 'number':
      if splitDataType[1] == 'decimal':
        DecimalPrecision = splitDataType[3]
        return unicode('%.' + DecimalPrecision + 'f') % Decimal(value)
      elif splitDataType[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint']:
        return u'%d' % int(value)
      elif splitDataType[1] in ['float', 'double']:
        try:
          return u'%f' % float(value)
        except Exception as Except:
          raise EDXMLValidationError("Invalid non-integer: '%s': %s" % (value, Except))
      else:
        # Must be hexadecimal
        return unicode(value.lower())
    elif splitDataType[0] == 'ip':
      try:
        octets = value.split('.')
      except Exception as Except:
        raise EDXMLValidationError("Invalid IP: '%s': %s" % (value, Except))
      else:
        try:
          return unicode('%d.%d.%d.%d' % tuple(int(octet) for octet in octets))
        except ValueError:
          raise EDXMLValidationError("Invalid IP: '%s'" % value)
    elif splitDataType[0] == 'geo':
      if splitDataType[1] == 'point':
        try:
          return u'%.6f,%.6f' % tuple(float(Coordinate) for Coordinate in value.split(','))
        except Exception as Except:
          raise EDXMLValidationError("Invalid geo:point: '%s': %s" % (value, Except))

    elif splitDataType[0] == 'string':
      if splitDataType[2] == 'ci':
        value = value.lower()
      return unicode(value)
    elif splitDataType[0] == 'boolean':
      return unicode(value.lower())
    else:
      return unicode(value)

  def Validate(self):
    """

    Validates the data type definition, raising an
    EDXMLValidationException when the definition is
    not valid.

    Raises:
      EDXMLValidationError
    Returns:
       DataType:
    """
    splitDataType = self.type.split(':')

    if splitDataType[0] == 'enum':
      if len(splitDataType) > 1:
        return self
    elif splitDataType[0] == 'timestamp':
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
          if len(splitDataType) > 3:
            try:
              hexLength = int(splitDataType[2])
              digitGroupLength = int(splitDataType[3])
            except ValueError:
              pass
            else:
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
