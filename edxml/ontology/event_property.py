# -*- coding: utf-8 -*-

from edxml.EDXMLWriter import EDXMLWriter

class EventProperty(object):
  """
  Class representing an EDXML event property
  """

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

  def __init__(self, Name, ObjectTypeName, Description = None, DefinesEntity = False, EntityConfidence = 0, Unique = False, Merge ='drop', Similar =''):

    self._attr = {
      'name':              Name,
      'object-type':       ObjectTypeName,
      'description' :      Description or Name,
      'defines-entity':    bool(DefinesEntity),
      'entity-confidence': float(EntityConfidence),
      'unique':            bool(Unique),
      'merge':             Merge,
      'similar':           Similar
    }

  @classmethod
  def Create(cls, Name, ObjectTypeName, Description = None):
    """

    Create a new event property.

    Note:
       The description should be really short, indicating
       which role the object has in the event type.

    Args:
      Name (str): Property name
      ObjectTypeName (str): Name of the object type
      Description (str): Property description

    Returns:
      EventProperty: The EventProperty instance
    """
    return cls(Name, ObjectTypeName, Description)

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

  def Write(self, Writer):
    """

    Writes the property into the provided
    EDXMLWriter instance.

    Args:
      Writer (EDXMLWriter): EDXMLWriter instance

    Returns:
      EventProperty: The EventProperty instance
    """
    Writer.AddEventProperty(self._attr['name'], self._attr['object-type'],self._attr['description'],self._attr['defines-entity'],self._attr['entity-confidence'],self._attr['unique'],self._attr['merge'], self._attr['similar'])

    return self
