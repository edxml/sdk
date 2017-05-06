# -*- coding: utf-8 -*-
from lxml import etree
from typing import Any
from typing import Dict

import edxml


class Concept(object):
  NAME_PATTERN = ...
  DISPLAY_NAME_PATTERN = ...
  FUZZY_MATCHING_PATTERN = ...

  def __init__(self, Ontology: edxml.ontology.Ontology, Name: str, DisplayName: str, Description: str = None) -> None:
    self._attr = ... # type: Dict[str, Any]

  def _childModifiedCallback(self, child) -> 'Concept': ...

  def GetName(self) -> str: ...

  def GetDisplayName(self) -> str: ...

  def GetDisplayNameSingular(self) -> str: ...

  def GetDisplayNamePlural(self) -> str: ...

  def GetDescription(self) -> str: ...

  def SetDescription(self, Description: str) -> 'Concept': ...

  def SetDisplayName(self, Singular: str, Plural: str = None) -> 'Concept': ...

  def Validate(self) -> 'Concept': ...

  @classmethod
  def Read(cls, typeElement: etree.Element, ontology: edxml.ontology.Ontology) -> 'Concept': ...

  def Update(self, concept: 'Concept') -> 'Concept': ...

  def GenerateXml(self) -> etree.Element: ...
