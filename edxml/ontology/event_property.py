# -*- coding: utf-8 -*-
from lxml import etree

import re

from edxml.EDXMLBase import EDXMLValidationError
import edxml.ontology


class EventProperty(object):
  """
  Class representing an EDXML event property
  """

  EDXML_PROPERTY_NAME_PATTERN = re.compile('^[a-z0-9-]{1,64}$')

  MERGE_MATCH = 'match'
  """Merge strategy 'match'"""
  MERGE_DROP = 'drop'
  """Merge strategy 'drop'"""
  MERGE_ADD = 'add'
  """Merge strategy 'add'"""
  MERGE_REPLACE = 'replace'
  """Merge strategy 'replace'"""
  MERGE_INC = 'increment'
  """Merge strategy 'increment'"""
  MERGE_SUM = 'sum'
  """Merge strategy 'sum'"""
  MERGE_MULTIPLY = 'multiply'
  """Merge strategy 'multiply'"""
  MERGE_MIN = 'min'
  """Merge strategy 'min'"""
  MERGE_MAX = 'max'
  """Merge strategy 'max'"""

  def __init__(self, eventType, Name, ObjectType, Description = None, DefinesEntity = False, EntityConfidence = 0, Unique = False, Merge ='drop', Similar =''):

    self._attr = {
      'name':              Name,
      'object-type':       ObjectType.GetName(),
      'description' :      Description or Name,
      'defines-entity':    bool(DefinesEntity),
      'entity-confidence': float(EntityConfidence),
      'unique':            bool(Unique),
      'merge':             Merge,
      'similar':           Similar
    }

    self._eventType = eventType  # type: edxml.ontology.EventType
    self._objectType = ObjectType  # type: edxml.ontology.ObjectType
    self._dataType = ObjectType.GetDataType()  # type: edxml.ontology.ObjectType

  def _setEventType(self, eventType):
    self._eventType = eventType
    return self


  def GetName(self):
    """

    Returns the property name.

    Returns:
      str:
    """
    return self._attr['name']

  def GetDescription(self):
    """

    Returns the property description.

    Returns:
      str:
    """
    return self._attr['description']

  def GetObjectTypeName(self):
    """

    Returns the name of the associated object type.

    Returns:
      str:
    """
    return self._attr['object-type']

  def GetMergeStrategy(self):
    """

    Returns the merge strategy.

    Returns:
      str:
    """
    return self._attr['merge']

  def GetEntityConfidence(self):
    """

    Returns the entity identification confidence.

    Returns:
      float:
    """
    return self._attr['entity-confidence']

  def GetSimilarHint(self):
    """

    Get the EDXML 'similar' attribute.

    Returns:
      str:
    """
    return self._attr['similar']

  def GetDataType(self):
    return self._dataType

  def RelateTo(self, TypePredicate, TargetPropertyName, Reason=None, Confidence=1.0, Directed=True):
    """

    Creates and returns a relation between this property and
    the specified target property.

    When no reason is specified, the reason is constructed by
    wrapping the type predicate with the place holders for
    the two properties.

    Args:
      TypePredicate (str): free form predicate
      TargetPropertyName (str): Name of the related property
      Reason (str): Relation description, with property placeholders
      Confidence (float): Relation confidence [0.0,1.0]
      Directed (bool): Directed relation True / False

    Returns:
      EventPropertyRelation: The EventPropertyRelation instance

    """
    return self._eventType.CreateRelation(
      self.GetName(), TargetPropertyName,
      Reason or '%s %s %s' % (self.GetName(), TypePredicate, TargetPropertyName),
      'other', TypePredicate, Confidence, Directed
    )

  def RelateInter(self, TypePredicate, TargetPropertyName, Reason=None, Confidence=1.0, Directed=True):
    """

    Creates and returns a relation between this property and
    the specified target property. The relation is an 'inter'
    relation, indicating that the related objects belong to
    different, related entities.

    When no reason is specified, the reason is constructed by
    wrapping the type predicate with the place holders for
    the two properties.

    Args:
      TypePredicate (str): free form predicate
      TargetPropertyName (str): Name of the related property
      Reason (str): Relation description, with property placeholders
      Confidence (float): Relation confidence [0.0,1.0]
      Directed (bool): Directed relation True / False

    Returns:
      EventPropertyRelation: The EventPropertyRelation instance

    """
    return self._eventType.CreateRelation(
      self.GetName(), TargetPropertyName,
      Reason or '%s %s %s' % (self.GetName(), TypePredicate, TargetPropertyName),
      'inter', TypePredicate, Confidence, Directed
    )

  def RelateIntra(self, TypePredicate, TargetPropertyName, Reason=None, Confidence=1.0, Directed=True):
    """

    Creates and returns a relation between this property and
    the specified target property. The relation is an 'intra'
    relation, indicating that the related objects belong to
    the same entity.

    When no reason is specified, the reason is constructed by
    wrapping the type predicate with the place holders for
    the two properties.

    Args:
      TargetPropertyName (str): Name of the related property
      Reason (str): Relation description, with property placeholders
      TypePredicate (str): free form predicate
      Confidence (float): Relation confidence [0.0,1.0]
      Directed (bool): Directed relation True / False

    Returns:
      EventPropertyRelation: The EventPropertyRelation instance

    """
    return self._eventType.CreateRelation(
      self.GetName(), TargetPropertyName,
      Reason or '%s %s %s' % (self.GetName(), TypePredicate, TargetPropertyName),
      'intra', TypePredicate, Confidence, Directed
    )

  def SetMergeStrategy(self, MergeStrategy):
    """

    Set the merge strategy of the property. This should
    be one of the MERGE_* attributes of this class.

    Args:
      MergeStrategy (str): The merge strategy

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = MergeStrategy

    if MergeStrategy == 'match':
      self._attr['unique'] = True

    return self

  def SetDescription(self, Description):
    """

    Set the description of the property. This should
    be really short, indicating which role the object
    has in the event type.

    Args:
      Description (str): The property description

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['description'] = Description
    return self

  def Unique(self):
    """

    Mark property as a unique property, which also sets
    the merge strategy to 'match'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['unique'] = True
    self._attr['merge'] = 'match'
    return self

  def IsUnique(self):
    """

    Returns True if property is unique, returns False otherwise

    Returns:
      bool:
    """
    return self._attr['unique']

  def Entity(self, Confidence):
    """

    Marks the property as an entity identifying
    property, with specified confidence.

    Args:
      Confidence (float): entity identification confidence [0.0, 1.0]

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['defines-entity'] = True
    self._attr['entity-confidence'] = float(Confidence)
    return self

  def IsEntity(self):
    """

    Returns True if property is an entity identifying
    property, returns False otherwise.

    Returns:
      bool:
    """
    return self._attr['defines-entity']
  def HintSimilar(self, Similarity):
    """

    Set the EDXML 'similar' attribute.

    Args:
      Similarity (str): similar attribute string

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['similar'] = Similarity
    return self

  def MergeAdd(self):
    """

    Set merge strategy to 'add'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'add'
    return self

  def MergeReplace(self):
    """

    Set merge strategy to 'replace'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'replace'
    return self

  def MergeDrop(self):
    """

    Set merge strategy to 'drop', which is
    the default merge strategy.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'drop'
    return self

  def MergeMin(self):
    """

    Set merge strategy to 'min'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'min'
    return self

  def MergeMax(self):
    """

    Set merge strategy to 'max'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'max'
    return self

  def MergeIncrement(self):
    """

    Set merge strategy to 'increment'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'increment'
    return self

  def MergeSum(self):
    """

    Set merge strategy to 'sum'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'sum'
    return self

  def MergeMultiply(self):
    """

    Set merge strategy to 'multiply'.

    Returns:
      EventProperty: The EventProperty instance
    """
    self._attr['merge'] = 'multiply'
    return self

  def Validate(self):
    """

    Checks if the property definition is valid. It only looks
    at the attributes of the property itself. Since it does
    not have access to the full ontology, the context of
    the property is not considered. For example, it does not
    check if the object type in the property actually exist.

    Raises:
      EDXMLValidationError
    Returns:
      EventProperty: The EventProperty instance

    """
    if not re.match(self.EDXML_PROPERTY_NAME_PATTERN, self._attr['name']):
      raise EDXMLValidationError('Invalid property name in property definition: "%s"' % self._attr['name'])

    if not re.match(edxml.ontology.ObjectType.NAME_PATTERN, self._attr['object-type']):
      raise EDXMLValidationError('Invalid object type name in property definition: "%s"' % self._attr['object-type'])

    if not len(self._attr['description']) <= 128:
      raise EDXMLValidationError('Property description is too long: "%s"' % self._attr['description'])

    if not len(self._attr['similar']) <= 64:
      raise EDXMLValidationError('Property attribute is too long: similar="%s"' % self._attr['similar'])

    if not self._attr['merge'] in ('drop', 'add', 'replace', 'min', 'max', 'increment', 'sum', 'multiply', 'match'):
      raise EDXMLValidationError('Invalid property merge strategy: "%s"' % self._attr['merge'])

    return self

  @classmethod
  def Read(cls, propertyElement, parentEventType):
    name = propertyElement.attrib['name']
    objectTypeName = propertyElement.attrib['object-type']
    objectType = parentEventType._ontology.GetObjectType(objectTypeName)

    if not objectType:
      raise EDXMLValidationError(
        'Property "%s" of event type "%s" refers to undefined object type "%s".' %
        (name, parentEventType.GetName(), objectTypeName)
      )

    return cls(
      parentEventType,
      propertyElement.attrib['name'],
      objectType,
      propertyElement.attrib['description'],
      propertyElement.get('defines-entity', 'false') == 'true',
      propertyElement.get('entity-confidence', 0),
      propertyElement.get('unique', 'false') == 'true',
      propertyElement.get('merge', 'drop'),
      propertyElement.get('similar', '')
    )

  def Update(self, eventProperty):
    """

    Updates the event property to match the EventProperty
    instance passed to this method, returning the
    updated instance.

    Args:
      eventProperty (EventProperty): The new EventProperty instance

    Returns:
      EventProperty: The updated EventProperty instance

    """
    if self._attr['name'] != eventProperty.GetName():
      raise Exception('Attempt to update event property "%s" with event property "%s".',
                      (self._attr['name'], eventProperty.GetName()))

    if self._attr['description'] != eventProperty.GetDescription():
      raise Exception('Attempt to update event property "%s", but descriptions do not match.',
                      (self._attr['name'], eventProperty.GetName()))

    self.Validate()

    return self

  def GenerateXml(self):
    """

    Generates an lxml etree Element representing
    the EDXML <property> tag for this event property.

    Returns:
      etree.Element: The element

    """

    attribs = dict(self._attr)

    attribs['defines-entity'] = 'true' if self._attr['defines-entity'] else 'false'
    attribs['entity-confidence'] = '%1.2f' % self._attr['entity-confidence']
    attribs['unique'] = 'true' if self._attr['unique'] else 'false'

    return etree.Element('property', attribs)
