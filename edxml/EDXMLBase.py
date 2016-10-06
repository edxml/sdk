# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                     Several commonly used Python classes.
#
#                  Copyright (c) 2010 - 2016 by D.H.J. Takken
#                          (d.h.j.takken@xs4all.nl)
#
#          This file is part of the EDXML Software Development Kit (SDK).
#
#
#  The EDXML SDK is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  The EDXML SDK is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with the EDXML SDK.  If not, see <http://www.gnu.org/licenses/>.
#
#
#  ===========================================================================

"""This module contains generic (base)classes used throughout the SDK."""
import traceback
from decimal import *
import sys
import re

class EDXMLError(Exception):
  """Generic EDXML exception class"""

  def __init__(self, message):
    self.Trace = ''.join(traceback.format_stack())
    super(Exception, self).__init__(message)

  def GetStackTrace(self):
    return self.Trace


class EDXMLProcessingInterrupted(Exception):
  """Exception for signaling that EDXML processing was aborted"""
  pass

class EDXMLBase(object):
  """Base class for most SDK subclasses"""

  def __init__(self):

    self.WarningCount = 0
    self.ErrorCount = 0

    # Expression used for matching SHA1 hashlinks
    self.HashlinkPattern = re.compile("^[0-9a-zA-Z]{40}$")
    # Expression used for matching string datatypes
    self.StringDataTypePattern = re.compile("string:[0-9]+:((cs)|(ci))(:[ru]+)?")
    # Expression used for matching binstring datatypes
    self.BinstringDataTypePattern = re.compile("binstring:[0-9]+(:r)?")
    # Expression used to find placeholders in event reporter strings
    self.PlaceHolderPattern = re.compile("\[\[([^\]]*)\]\]")

  def Error(self, Message):
    """Raises :class:`EDXMLError`.

    Args:
      Message (str): Error message
    """

    self.ErrorCount += 1
    raise EDXMLError(unicode("ERROR: " + Message).encode('utf-8'))

  def Warning(self, Message):
    """Prints a warning to sys.stderr.

    Args:
      Message (str): Warning message

    """
    self.WarningCount += 1
    sys.stderr.write(unicode("WARNING: " + Message + "\n").encode('utf-8'))

  def GetWarningCount(self):
    """Returns the number of warnings generated"""
    return self.WarningCount

  def GetErrorCount(self):
    """Returns the number of errors generated"""
    return self.ErrorCount

  def ValidateDataType(self, ObjectType, DataType):
    """Validate a data type.

    Args:
      ObjectType (str): Name of the object type having specified data type

      DataType (str):   EDXML data type

    calls :func:`Error` when datatype is invalid.

    """

    SplitDataType = DataType.split(':')

    if SplitDataType[0] == 'enum':
      if len(SplitDataType) > 1:
        return
    elif SplitDataType[0] == 'timestamp':
      if len(SplitDataType) == 1:
        return
    elif SplitDataType[0] == 'ip':
      if len(SplitDataType) == 1:
        return
    elif SplitDataType[0] == 'hashlink':
      if len(SplitDataType) == 1:
        return
    elif SplitDataType[0] == 'boolean':
      if len(SplitDataType) == 1:
        return
    elif SplitDataType[0] == 'geo':
      if len(SplitDataType) == 2:
        if SplitDataType[1] == 'point':
          return
    elif SplitDataType[0] == 'number':
      if len(SplitDataType) >= 2:
        if SplitDataType[1] in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint', 'float', 'double']:
          if len(SplitDataType) == 3:
            if SplitDataType[2] == 'signed':
              return
          else:
            return
        elif SplitDataType[1] == 'decimal':
          if len (SplitDataType) >= 4:
            try:
              int(SplitDataType[2])
              int(SplitDataType[3])
            except:
              pass
            else:
              if int(SplitDataType[3]) > int(SplitDataType[2]):
                self.Error("Invalid Decimal: " + DataType)
              if len (SplitDataType) > 4:
                if len (SplitDataType) == 5:
                  if SplitDataType[4] == 'signed':
                    return
              else:
                return
        elif SplitDataType[1] == 'hex':
          if len(SplitDataType) > 3:
            try:
              HexLength        = int(SplitDataType[2])
              DigitGroupLength = int(SplitDataType[3])
            except:
              pass
            else:
              if HexLength % DigitGroupLength != 0:
                self.Error("Length of hex datatype is not a multiple of separator distance: " + DataType)
              if len(SplitDataType[4]) == 0:
                if len(SplitDataType) == 6:
                  # This happens if the colon ':' is used as separator
                  return
              else:
                return
          else:
            return
    elif SplitDataType[0] == 'string':
      if re.match(self.StringDataTypePattern, DataType):
        return
    elif SplitDataType[0] == 'binstring':
      if re.match(self.BinstringDataTypePattern, DataType):
        return

    self.Error("EDXMLBase::ValidateDataType: Object type %s has an unsupported data type: %s" % (( ObjectType, DataType )) )

  def ValidateObject(self, Value, ObjectTypeName, DataType, Regexp = None):
    """Validate an object value.

    The Value argument can be a string, int, bool, Decimal, etc depending on the data type.

    Args:
      Value: Object value.

      ObjectTypeName (str): Object type.

      DataType (str): EDXML data type of object.

      Regexp (str, optional): Regular expression for checking Value.

    calls :func:`Error` when value is invalid.

    """

    ObjectDataType = DataType.split(':')

    if ObjectDataType[0] == 'timestamp':
      try:
        float(Value)
      except:
        self.Error("Invalid timestamp '%s' of object type %s." % (( str(Value), ObjectTypeName )))
    elif ObjectDataType[0] == 'number':
      if ObjectDataType[1] == 'decimal':
        if len(ObjectDataType) < 5:
          # Decimal is unsigned.
          if Decimal(Value) < 0:
            self.Error("Unsigned decimal value '%s' of object type %s is negative." % (( str(Value), ObjectTypeName )))
      elif ObjectDataType[1] == 'hex':
        if len(ObjectDataType) > 3:
          HexSeparator = ObjectDataType[4]
          if len(HexSeparator) == 0 and len(ObjectDataType) == 6:
            HexSeparator = ':'
          Value = ''.join(c for c in str(Value) if c != HexSeparator)
        try:
          Value.decode("hex")
        except:
          self.Error("Invalid hexadecimal value '%s' of object type %s." % (( str(Value), ObjectTypeName )))
      elif ObjectDataType[1] == 'float' or ObjectDataType[1] == 'double':
        try:
          float(Value)
        except:
          self.Error("Invalid number '%s' of object type %s." % (( str(Value), ObjectTypeName )))
        if len(ObjectDataType) < 3:
          # number is unsigned.
          if Value < 0:
            self.Error("Unsigned float or double value '%s' of object type %s is negative." % (( str(Value), ObjectTypeName )))
      else:
        try:
          int(Value)
        except:
          self.Error("Invalid number '%s' of object type %s." % (( str(Value), ObjectTypeName )))
        if len(ObjectDataType) < 3:
          # number is unsigned.
          if Value < 0:
            self.Error("Unsigned integer value '%s' of object type %s is negative." % (( str(Value), ObjectTypeName )))
    elif ObjectDataType[0] == 'geo':
      if ObjectDataType[1] == 'point':
        # This is the only option at the moment.
        SplitGeoPoint = Value.split(',')
        if len(SplitGeoPoint) != 2:
          self.Error("The geo:point value '%s' is not formatted correctly." % str(Value))
        try:
          GeoLat = float(SplitGeoPoint[0])
          GeoLon = float(SplitGeoPoint[1])
        except:
          self.Error("The geo:point value '%s' is not formatted correctly." % str(Value))
          return
        if GeoLat < -90 or GeoLat > 90:
          self.Error("The geo:point value '%s' contains a latitude that is not within range [-90,90]." % str(Value))
        if GeoLon < -180 or GeoLon > 180:
          self.Error("The geo:point value '%s' contains a longitude that is not within range [-180,180]." % str(Value))
      else:
        self.Error("Invalid geo data type: '%s'" % str(DataType) )
    elif ObjectDataType[0] == 'string':
      # First, we check if value is a unicode
      # string. If not, we convert it to unicode.
      if not isinstance(Value, unicode):
        if not isinstance(Value, str):
          self.Warning("EDXMLBase::ValidateObject: Expected a string, but passed value is no string: '%s'" % str(Value) )
          Value = str(Value)
        try:
          Value = Value.decode('utf-8')
        except UnicodeDecodeError:
          # String is not proper UTF8. Lets try to decode it as Latin1
          try:
            Value = Value.decode('latin-1').encode('utf-8')
          except ValueError:
            Value = unicode(Value, errors='replace')
            self.Warning("EDXMLBase::ValidateObject: Failed to convert value to unicode: '%s'. Some characters were replaced by the Unicode replacement character." % repr(Value) )

      # Check if data type matches regexp pattern
      if not re.match(self.StringDataTypePattern, DataType):
        self.Error("EDXMLBase::ValidateObject: Invalid string data type: %s" % DataType)

      # Check length of object value
      if Value == '':
        self.Error("EDXMLBase::ValidateObject: Value of %s object is empty." % ObjectTypeName)
      MaxStringLength = int(ObjectDataType[1])
      if MaxStringLength > 0:
        if len(Value) > MaxStringLength:
          self.Error("EDXMLBase::ValidateObject: string too long for object type %s: '%s'" % (( ObjectTypeName, Value )))

      # Check character set of object value
      if len(ObjectDataType) < 4 or 'u' not in ObjectDataType[3]:
        # String should only contain latin1 characters.
        try:
          unicode(Value).encode('latin1')
        except:
          self.Error("EDXMLBase::ValidateObject: string of latin1 objecttype %s contains unicode characters: %s" % (( ObjectTypeName, Value )))
      if Regexp:
        if len(ObjectDataType) >= 4 and 'i' in ObjectDataType[3]:
          # Perform regex matching on lower case string
          Value = Value.lower()
        if not re.match(Regexp, Value):
          self.Error("EDXMLBase::ValidateObject: Object value '%s' of object type %s does not match regexp '%s' of the object type." % (( Value, ObjectTypeName, Regexp.pattern )) )
    elif ObjectDataType[0] == 'binstring':
      # Check if data type matches regexp pattern
      if not re.match(self.BinstringDataTypePattern, DataType):
        self.Error("EDXMLBase::ValidateObject: Invalid binstring data type: %s" % DataType)
      if ObjectDataType[1] > 0 and len(Value) > ObjectDataType[1]:
          self.Error("EDXMLBase::ValidateObject: binstring too long for object type %s: '%s'" % (( ObjectTypeName, Value )))
    elif ObjectDataType[0] == 'hashlink':
      if not re.match(self.HashlinkPattern, Value):
        self.Error("EDXMLBase::ValidateObject: Invalid hashlink: '%s'" % str(Value) )
    elif ObjectDataType[0] == 'ip':
      SplitIp = Value.split('.')
      if len(SplitIp) != 4:
        self.Error("EDXMLBase::ValidateObject: Invalid IP address: '%s'" % str(Value) )
      for SplitIpPart in SplitIp:
        try:
          if not 0 <= int(SplitIpPart) <= 255:
            self.Error("EDXMLBase::ValidateObject: Invalid IP address: '%s'" % str(Value) )
        except:
            self.Error("EDXMLBase::ValidateObject: Invalid IP address: '%s'" % str(Value) )
    elif ObjectDataType[0] == 'boolean':
      try:
        ObjectString = Value.lower()
        if ObjectString in ['true', 'false']:
          return
      except AttributeError:
        pass
      self.Error("EDXMLBase::ValidateObject: Invalid boolean: '%s'" % str(Value))
    elif ObjectDataType[0] == 'enum':
      if not Value in ObjectDataType[1:]:
        self.Error("EDXMLBase::ValidateObject: Invalid value for enum data type: '%s'" % str(Value) )
    else:
      self.Error("EDXMLBase::ValidateObject: Invalid data type: '%s'" % str(DataType) )

  def NormalizeObject(self, Value, DataType):
    """Normalize an object value to a unicode string

    Prepares an object value for computing sticky hashes, by
    applying the normalization rules as outlined in the EDXML
    specification. It takes a string containing an object value
    as input and returns a normalized unicode string.

    Args:
      Value (str, unicode): The input object value

      DataType (str): EDXML data type

    Returns:
      unicode. The normalized object value

    calls :func:`Error` when value is invalid.
    """
    if DataType[0] == 'timestamp':
      return u'%.6f' % Decimal(Value)
    elif DataType[0] == 'number':
      if DataType[1] == 'decimal':
        DecimalPrecision = DataType[3]
        return unicode('%.' + DecimalPrecision + 'f') % Decimal(Value)
      elif DataType[1] in [ 'tinyint', 'smallint', 'mediumint', 'int', 'bigint']:
        return u'%d' % int(Value)
      elif DataType[1] in ['float', 'double']:
        try:
          return u'%f' % float(Value)
        except Exception as Except:
          self.Error("NormalizeObject: Invalid non-integer: '%s': %s" % (( Value, Except )))
      else:
        # Must be hexadecimal
        return unicode(Value.lower())
    elif DataType[0] == 'ip':
      try:
        Octets = Value.split('.')
      except Exception as Except:
        self.Error("NormalizeObject: Invalid IP: '%s': %s" % (( Value, Except )))
      else:
        try:
          return unicode('%d.%d.%d.%d' % (( int(Octets[0]), int(Octets[1]), int(Octets[2]), int(Octets[3]) ))  )
        except:
          self.Error("NormalizeObject: Invalid IP: '%s'" % Value)
    elif DataType[0] == 'geo':
      if DataType[1] == 'point':
        try:
          return u'%.6f,%.6f' % tuple(float(Coordinate) for Coordinate in Value.split(','))
        except Exception as Except:
          self.Error("NormalizeObject: Invalid geo:point: '%s': %s" % (( Value, Except )))

    elif DataType[0] == 'string':

      if not isinstance(Value, unicode):
        if not isinstance(Value, str):
          self.Warning("NormalizeObject: Expected a string, but passed value is no string: '%s'" % str(Value) )
          Value = unicode(Value)
        try:
          Value = Value.decode('utf-8')
        except UnicodeDecodeError:
          # String is not proper UTF8. Lets try to decode it as Latin1
          try:
            Value = Value.decode('latin-1').encode('utf-8').decode('utf-8')
          except:
            self.Error("NormalizeObject: Failed to convert string object to unicode: '%s'." % repr(Value) )

      if DataType[2] == 'ci':
        Value = Value.lower()
      return unicode(Value)
    elif DataType[0] == 'boolean':
      return unicode(Value.lower())
    else:
      return unicode(Value )
