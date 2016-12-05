# -*- coding: utf-8 -*-
import re

from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import EventProperty
import edxml.ontology


class PropertyRelation(object):
  """
  Class representing a relation between two EDXML properties
  """

  def __init__(self, Source, Dest, Description, TypeClass, TypePredicate, Confidence = 1.0, Directed = True):

    self._attr = {
      'property1':         Source,
      'property2':         Dest,
      'description':       Description,
      'type':              '%s:%s' % (TypeClass, TypePredicate),
      'confidence':        float(Confidence),
      'directed':          bool(Directed),
    }

  @classmethod
  def Create(cls, Source, Dest, Description, TypeClass, TypePredicate, Confidence = 1.0, Directed = True):
    """

    Create a new property relation

    Args:
      Source (str): Name of source property
      Dest (str): Name of destination property
      Description (str): Relation description, with property placeholders
      TypeClass (str): Relation type class ('inter', 'intra' or 'other')
      TypePredicate (str): free form predicate
      Confidence (float): Relation confidence [0.0,1.0]
      Directed (bool): Directed relation True / False

    Returns:
      PropertyRelation:
    """
    return cls(Source, Dest, Description, TypeClass, TypePredicate, Confidence, Directed)

  def GetSource(self):
    """

    Returns the name of the source property.

    Returns:
      str:
    """
    return self._attr['property1']

  def GetDest(self):
    """

    Returns the name of the destination property.

    Returns:
      str:
    """
    return self._attr['property1']

  def GetDescription(self):
    """

    Returns the relation description.

    Returns:
      str:
    """
    return self._attr['description']

  def GetType(self):
    """

    Returns the relation type.

    Returns:
      str:
    """
    return self._attr['type']

  def GetTypeClass(self):
    """

    Returns the class part of the relation type.

    Returns:
      str:
    """
    return self._attr['type'].split(':')[0]

  def GetTypePredicate(self):
    """

    Returns the predicate part of the relation type.

    Returns:
      str:
    """
    return self._attr['type'].split(':')[1]

  def GetConfidence(self):
    """

    Returns the relation confidence.

    Returns:
      float:
    """
    return self._attr['confidence']

  def IsDirected(self):
    """

    Returns True when the relation is directed,
    returns False otherwise.

    Returns:
      bool:
    """
    return self._attr['directed']

  def SetConfidence(self, Confidence):
    """

    Configure the relation confidence

    Args:
     Confidence (float): Relation confidence [0.0,1.0]

    Returns:
      PropertyRelation: The PropertyRelation instance
    """

    self._attr['confidence'] = float(Confidence)
    return self

  def Directed(self):
    """

    Marks the property relation as directed

    Returns:
      PropertyRelation: The PropertyRelation instance
    """
    self._attr['directed'] = True
    return self

  def Undirected(self):
    """

    Marks the property relation as undirected

    Returns:
      PropertyRelation: The PropertyRelation instance
    """
    self._attr['directed'] = False
    return self

  def Validate(self):
    """

    Checks if the property relation is valid. It only looks
    at the attributes of the relation itself. Since it does
    not have access to the full ontology, the context of
    the relation is not considered. For example, it does not
    check if the properties in the relation actually exist.

    Raises:
      EDXMLValidationError
    Returns:
      PropertyRelation: The PropertyRelation instance

    """
    if not re.match(EventProperty.EDXML_PROPERTY_NAME_PATTERN, self._attr['property1']):
      raise EDXMLValidationError('Invalid property name in property relation: "%s"' % self._attr['property1'])

    if not re.match(EventProperty.EDXML_PROPERTY_NAME_PATTERN, self._attr['property2']):
      raise EDXMLValidationError('Invalid property name in property relation: "%s"' % self._attr['property2'])

    if not len(self._attr['description']) <= 255:
      raise EDXMLValidationError('Property relation description is too long: "%s"' % self._attr['description'])

    if not re.match('^(intra|inter|parent|child|other):.+', self._attr['type']):
      raise EDXMLValidationError('Invalid property relation type: "%s"' % self._attr['type'])

    placeholders = re.findall(edxml.ontology.EventType.REPORTER_PLACEHOLDER_PATTERN, self._attr['description'])

    if not self._attr['property1'] in placeholders:
      raise EDXMLValidationError(
        'Relation between properties %s and %s has a description that does not refer to property %s: "%s"' %
        (self._attr['property1'], self._attr['property2'], self._attr['property1'], self._attr['description'])
      )

    if not self._attr['property2'] in placeholders:
      raise EDXMLValidationError(
        'Relation between properties %s and %s has a description that does not refer to property %s: "%s"' %
        (self._attr['property1'], self._attr['property2'], self._attr['property2'], self._attr['description'])
      )

    for propertyName in placeholders:
      if propertyName not in (self._attr['property1'], self._attr['property2']):
        raise EDXMLValidationError(
          'Relation between properties %s and %s has a description that refers to other properties: "%s"' %
          (self._attr['property1'], self._attr['property2'], self._attr['description'])
        )

    return self

  @classmethod
  def Read(cls, relationElement):
    return cls(
      relationElement.attrib['property1'],
      relationElement.attrib['property2'],
      relationElement.attrib['description'],
      relationElement.attrib['type'].split(':')[0],
      relationElement.attrib['type'].split(':')[1],
      float(relationElement.attrib.get('confidence', '1')),
      relationElement.get('directed', 'true') == 'true'
    )

  def Write(self, Writer):
    """

    Writes the property relation into the provided
    EDXMLWriter instance

    Args:
      Writer (EDXMLWriter): EDXMLWriter instance

    Returns:
      PropertyRelation: The PropertyRelation instance
    """

    Writer.AddRelation(self._attr['property1'], self._attr['property2'], self._attr['type'], self._attr['description'], self._attr['confidence'], self._attr['directed'])

    return self
