# -*- coding: utf-8 -*-
import edxml

from typing import List, Dict, Iterable
from lxml import etree


class EventType(object):

    NAME_PATTERN = ...
    DISPLAY_NAME_PATTERN = ...
    CLASS_LIST_PATTERN = ...
    TEMPLATE_PATTERN = ...
    KNOWN_FORMATTERS = ...  # type: List[str]

    def __init__(self, Ontology: edxml.ontology.Ontology, Name: str, DisplayName: str = None, Description: str = None,
                 ClassList: str = '', Summary: str = 'no description available',
                 Story: str = 'no description available', Parent: edxml.ontology.EventTypeParent = None) -> None:

        self._attr = ...              # type: Dict
        self._properties = ...        # type: Dict[str, edxml.ontology.EventProperty]
        self._relations = ...         # type: List[edxml.ontology.PropertyRelation]
        self._parent = ...            # type: edxml.ontology.EventTypeParent
        self._parentDescription = ...  # type: str
        self._relaxNG = None          # type: etree.RelaxNG
        self._ontology = ...           # type: edxml.ontology.Ontology

        self.__cachedUniqueProperties = ...  # type: Dict[str, edxml.ontology.EventProperty]
        self.__cachedHashProperties = ...    # type: Dict[str, edxml.ontology.EventProperty]

    def __getitem__(self, propertyName: str) -> edxml.ontology.EventProperty: ...

    def _childModifiedCallback(self) -> 'EventType': ...

    def _setAttr(self, key: str, value): ...

    def GetName(self) -> str: ...

    def GetDescription(self) -> str: ...

    def GetDisplayNameSingular(self) -> str: ...

    def GetDisplayNamePlural(self) -> str: ...

    def GetClasses(self) -> List[str]: ...

    def GetProperties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def GetUniqueProperties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def GetHashProperties(self) -> Dict[str, edxml.ontology.EventProperty]: ...

    def GetPropertyRelations(self) -> List[edxml.ontology.PropertyRelation]: ...

    def HasClass(self, ClassName) -> bool: ...

    def IsUnique(self) -> bool: ...

    def GetSummaryTemplate(self) -> str: ...

    def GetStoryTemplate(self) -> str: ...

    def GetParent(self) -> edxml.ontology.EventTypeParent: ...

    def CreateProperty(self, Name: str, ObjectTypeName: str, Description: str = None) -> edxml.ontology.EventProperty: ...

    def AddProperty(self, Property: edxml.ontology.EventProperty) -> 'EventType': ...

    def RemoveProperty(self, propertyName: str) -> 'EventType': ...

    def CreateRelation(self, Source: str, Target: str, Description: str, TypeClass: str, TypePredicate: str, Confidence: float = 1.0, Directed: bool = True): ...

    def AddRelation(self, Relation: edxml.ontology.PropertyRelation) -> 'EventType': ...

    def MakeChildren(self, SiblingsDescription: str, Parent: 'EventType') -> edxml.ontology.EventTypeParent: ...

    def IsParent(self, ParentDescription, Child: 'EventType') -> 'EventType': ...

    def SetDescription(self, Description: str) -> 'EventType': ...

    def SetParent(self, Parent: edxml.ontology.EventTypeParent) -> 'EventType': ...

    def AddClass(self, ClassName: str) -> 'EventType': ...

    def SetClasses(self, ClassNames: Iterable[str]) -> 'EventType': ...

    def SetName(self, EventTypeName: str) -> 'EventType': ...

    def SetDisplayName(self, Singular: str, Plural: str = None) -> 'EventType': ...

    def SetSummaryTemplate(self, Summary: unicode) -> 'EventType': ...

    def SetStoryTemplate(self, Story: unicode) -> 'EventType': ...

    def ValidateTemplate(self, string: unicode, ontology: edxml.ontology.Ontology) -> 'EventType': ...

    def Validate(self) -> 'EventType': ...

    @classmethod
    def Read(cls, typeElement: etree.Element, ontology: edxml.ontology.Ontology) -> 'EventType': ...

    def Update(self, eventType: 'EventType') -> 'EventType': ...

    def GenerateXml(self) -> etree.Element: ...

    def GetSingularPropertyNames(self) -> List[str]: ...

    def GetMandatoryPropertyNames(self) -> List[str]: ...

    def validateEventStructure(self, edxmlEvent: edxml.EDXMLEvent) -> 'EventType': ...

    def validateEventObjects(self, edxmlEvent: edxml.EDXMLEvent) -> 'EventType': ...

    def generateRelaxNG(self, Ontology: edxml.ontology.Ontology) -> etree.ElementTree: ...
