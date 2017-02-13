# -*- coding: utf-8 -*-
from lxml import etree

import re

from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import EventProperty
import edxml.ontology


class PropertyRelation(object):
  """
  Class representing a relation between two EDXML properties
  """

  def __init__(self, EventType, Source, Dest, Description, TypeClass, TypePredicate, Confidence = 1.0, Directed = True):

    self._attr = {
      'property1':         Source.GetName(),
      'property2':         Dest.GetName(),
      'description':       Description,
      'type':              '%s:%s' % (TypeClass, TypePredicate),
      'confidence':        float(Confidence),
      'directed':          bool(Directed),
    }

    self._eventType = EventType  # type: edxml.ontology.EventType

  def _childModifiedCallback(self):
    """Callback for change tracking"""
    return self

  def GetSource(self):
    """

    Returns the source property.

    Returns:
      edxml.ontology.EventProperty:
    """
    return self._attr['property1']

  def GetTarget(self):
    """

    Returns the target property.

    Returns:
      edxml.ontology.EventProperty:
    """
    return self._attr['property2']

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

  def Because(self, Reason):
    """

    Sets the relation description to specified string,
    which should contain placeholders for the values
    of both related properties.

    Args:
      Reason (str): Relation description

    Returns:
      PropertyRelation: The PropertyRelation instance

    """
    self._attr['description'] = Reason
    return self

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
  def Read(cls, relationElement, eventType):
    source = relationElement.attrib['property1']
    target = relationElement.attrib['property2']

    for propertyName in (source, target):
      if propertyName not in eventType:
        raise EDXMLValidationError(
          'Event type "%s" contains a property relation referring to property "%s", which is not defined.' %
          (eventType.GetName(), propertyName))

    return cls(
      eventType,
      eventType[relationElement.attrib['property1']],
      eventType[relationElement.attrib['property2']],
      relationElement.attrib['description'],
      relationElement.attrib['type'].split(':')[0],
      relationElement.attrib['type'].split(':')[1],
      float(relationElement.attrib.get('confidence', '1')),
      relationElement.get('directed', 'true') == 'true'
    )

  def Update(self, propertyRelation):
    """

    Updates the property relation to match the PropertyRelation
    instance passed to this method, returning the
    updated instance.

    Args:
      propertyRelation (PropertyRelation): The new PropertyRelation instance

    Returns:
      PropertyRelation: The updated PropertyRelation instance

    """
    if self._attr['property1'] != propertyRelation.GetSource() or self._attr['property2'] != propertyRelation.GetDest():
      raise Exception('Attempt to property relation between %s -> %s with relation between %s -> %s.',
                      (self._attr['property1'], self._attr['property2'],
                       propertyRelation.GetSource(), propertyRelation.GetDest()))

    self.Validate()

    return self

  def GenerateXml(self):
    """

    Generates an lxml etree Element representing
    the EDXML <relation> tag for this event property.

    Returns:
      etree.Element: The element

    """

    attribs = dict(self._attr)

    attribs['confidence'] = '%1.2f' % self._attr['confidence']
    attribs['directed'] = 'true' if self._attr['directed'] else 'false'

    return etree.Element('relation', attribs)
