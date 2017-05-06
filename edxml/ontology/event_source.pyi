# -*- coding: utf-8 -*-
from datetime import datetime

from lxml import etree
from typing import Any
from typing import Dict

import edxml


class EventSource(object):

  SOURCE_URI_PATTERN = ...
  ACQUISITION_DATE_PATTERN = ...

  def __init__(self, Ontology: edxml.ontology.Ontology, Uri: str, Description: str = 'no description available', AcquisitionDate: str = '00000000') -> None:

    self._attr = ... # type: Dict[str, Any]

  def _childModifiedCallback(self, child) -> 'EventSource': ...

  def GetUri(self) -> str: ...

  def GetAcquisitionDateString(self) -> str: ...

  def SetDescription(self, Description: str) -> 'EventSource': ...

  def SetAcquisitionDate(self, dateTime: datetime.datetime): ...

  def Validate(self) -> 'EventSource': ...

  @classmethod
  def Read(cls, sourceElement: etree.Element, ontology: edxml.ontology.Ontology) -> 'EventSource': ...

  def Update(self, source: 'EventSource') -> 'EventSource': ...

  def GenerateXml(self) -> etree.Element: ...
