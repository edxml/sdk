# -*- coding: utf-8 -*-

class DataType(object):
  """
  Class representing an EDXML data type
  """

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

    Returns the EDXML data-type attribute.

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
