# -*- coding: utf-8 -*-

import edxml

from lxml import etree
from typing import Any
from typing import Dict


class EventProperty(object):

  EDXML_PROPERTY_NAME_PATTERN = ...

  MERGE_MATCH = ...
  """Merge strategy 'match'"""
  MERGE_DROP = ...
  """Merge strategy 'drop'"""
  MERGE_ADD = ...
  """Merge strategy 'add'"""
  MERGE_REPLACE = ...
  """Merge strategy 'replace'"""
  MERGE_SUM = ...
  """Merge strategy 'sum'"""
  MERGE_MULTIPLY = ...
  """Merge strategy 'multiply'"""
  MERGE_MIN = ...
  """Merge strategy 'min'"""
  MERGE_MAX = ...
  """Merge strategy 'max'"""

  def __init__(self, eventType: edxml.ontology.EventType, Name: str, ObjectType: edxml.ontology.ObjectType,
               Description: str = None, DefinesEntity: bool = False,
               EntityConfidence: float = 0, Enp: int = 128, Unique: bool = False, Merge: str ='drop', Similar: str ='') -> None:

    self._attr = ...       # type: Dict[str, Any]
    self._eventType = ...  # type: edxml.ontology.EventType
    self._objectType = ... # type: edxml.ontology.ObjectType

  def _childModifiedCallback(self) -> 'EventProperty': ...

  def _setAttr(self, key: str, value): ...

  def GetName(self) -> str: ...

  def GetDescription(self) -> str: ...

  def GetObjectTypeName(self) -> str: ...

  def GetMergeStrategy(self) -> str: ...

  def GetConceptConfidence(self) -> float: ...

  def GetConceptNamingPriority(self) -> int: ...

  def GetSimilarHint(self) -> str: ...

  def GetObjectType(self) -> edxml.ontology.ObjectType: ...

  def GetDataType(self) -> edxml.ontology.DataType: ...

  def RelateTo(self, TypePredicate: str, TargetPropertyName: str, Reason: str = None, Confidence: float = 1.0, Directed: bool = True) -> edxml.ontology.PropertyRelation: ...

  def RelateInter(self, TypePredicate: str, TargetPropertyName: str, Reason: str = None, Confidence: float = 1.0, Directed: bool = True) -> edxml.ontology.PropertyRelation: ...

  def RelateIntra(self, TypePredicate: str, TargetPropertyName: str, Reason: str = None,Confidence: float = 1.0, Directed: bool = True) -> edxml.ontology.PropertyRelation: ...

  def SetMergeStrategy(self, MergeStrategy: str) -> 'EventProperty': ...

  def SetDescription(self, Description: str) -> 'EventProperty': ...

  def Unique(self) -> 'EventProperty': ...

  def IsUnique(self) -> bool: ...

  def Identifies(self, ConceptName: str, Confidence: float) -> 'EventProperty': ...

  def SetConceptNamingPriority(self, Priority: int) -> 'EventProperty': ...

  def GetConceptName(self) -> str: ...

  def HintSimilar(self, Similarity: str) -> 'EventProperty': ...

  def MergeAdd(self) -> 'EventProperty': ...

  def MergeReplace(self) -> 'EventProperty': ...

  def MergeDrop(self) -> 'EventProperty': ...

  def MergeMin(self) -> 'EventProperty': ...

  def MergeMax(self) -> 'EventProperty': ...

  def MergeIncrement(self) -> 'EventProperty': ...

  def MergeSum(self) -> 'EventProperty': ...

  def MergeMultiply(self) -> 'EventProperty': ...

  def Validate(self) -> 'EventProperty': ...

  @classmethod
  def Read(cls, propertyElement : etree.Element, parentEventType: edxml.ontology.EventType) -> 'EventProperty': ...

  def Update(self, eventProperty: 'EventProperty') -> 'EventProperty': ...

  def GenerateXml(self) -> etree.Element: ...
