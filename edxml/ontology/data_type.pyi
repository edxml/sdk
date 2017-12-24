# -*- coding: utf-8 -*-
from datetime import datetime
from lxml import etree
from typing import List


class DataType(object):

  # Expression used for matching SHA1 hashlinks
  HASHLINK_PATTERN = ...
  # Expression used for matching string datatypes
  STRING_PATTERN = ...
  # Expression used for matching uri datatypes
  URI_PATTERN = ...

  def __init__(self, data_type: str) -> None:

    self.type = ... # type: str

  @classmethod
  def DateTime(cls) -> 'DataType': ...

  @classmethod
  def Boolean(cls) -> 'DataType': ...

  @classmethod
  def TinyInt(cls, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def SmallInt(cls, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def MediumInt(cls, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def Int(cls, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def BigInt(cls, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def Float(cls, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def Double(cls, Signed = True) -> 'DataType': ...

  @classmethod
  def Decimal(cls, TotalDigits: int, FractionalDigits: int, Signed: bool = True) -> 'DataType': ...

  @classmethod
  def String(cls, Length: int = 0, CaseSensitive: bool = True, RequireUnicode: bool = True, ReverseStorage: bool = False) -> 'DataType': ...

  @classmethod
  def Enum(cls, *Choices: str) -> 'DataType': ...

  @classmethod
  def Uri(cls, pathSeparator: str ='/') -> 'DataType': ...

  @classmethod
  def Hexadecimal(cls, Length: int, Separator: str = None, GroupSize: int = None) -> 'DataType': ...

  @classmethod
  def GeoPoint(cls) -> 'DataType': ...

  @classmethod
  def Hashlink(cls) -> 'DataType': ...

  @classmethod
  def Ipv4(cls) -> 'DataType': ...

  def Get(self) -> str: ...

  def GetFamily(self) -> str: ...

  def GetSplit(self) -> List[str]: ...

  def IsNumerical(self) -> bool: ...

  def IsDateTime(self) -> bool: ...

  def GenerateRelaxNG(self, RegExp: str) -> etree.Element: ...

  def NormalizeObjects(self, value: List[unicode]) -> List[unicode]: ...

  def ValidateObjectValue(self, value: unicode) -> 'DataType': ...

  def Validate(self) -> 'DataType': ...

  @classmethod
  def FormatUtcDateTime(cls, dateTime: datetime) -> str: ...
