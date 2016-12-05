# -*- coding: utf-8 -*-
import re

import edxml
from edxml.EDXMLBase import EDXMLValidationError

from edxml.EDXMLWriter import EDXMLWriter

class EventTypeParent(object):
  """
  Class representing an EDXML event type parent
  """

  PROPERTY_MAP_PATTERN = re.compile("^[a-z0-9-]{1,64}:[a-z0-9-]{1,64}(,[a-z0-9-]{1,64}:[a-z0-9-]{1,64})*$")

  def __init__(self, ParentEventTypeName, PropertyMap, ParentDescription = None, SiblingsDescription = None):

    self._attr = {
      'eventtype':          ParentEventTypeName,
      'propertymap':        ','.join(['%s:%s' % (Child, Parent) for Child, Parent in PropertyMap.items()]),
      'parent-description':   ParentDescription or 'belonging to',
      'siblings-description': SiblingsDescription or 'sharing'
    }

  @classmethod
  def Create(cls, ParentEventTypeName, PropertyMap, ParentDescription = None, SiblingsDescription = None):
    """

    Creates a new event type parent. The PropertyMap argument is a dictionary
    mapping property names of the child event type to property names of the
    parent event type.

    If no ParentDescription is specified, it will be set to 'belonging to'.
    If no SiblingsDescription is specified, it will be set to 'sharing'.

    Note:
       All unique properties of the parent event type must appear in
       the property map.

    Note:
       The parent event type must be defined in the same EDXML stream
       as the child.

    Args:
      ParentEventTypeName (str): Name of the parent event type
      PropertyMap (dict[str, str]): Property map
      ParentDescription (str, Optional): The EDXML parent-description attribute
      SiblingsDescription (str, Optional): The EDXML siblings-description attribute

    Returns:
      EventTypeParent: The EventTypeParent instance
    """
    return cls(ParentEventTypeName, PropertyMap, ParentDescription, SiblingsDescription)

  def SetParentDescription(self, Description):
    """
    Sets the EDXML parent-description attribute

    Args:
      Description (str): The EDXML parent-description attribute

    Returns:
      EventTypeParent: The EventTypeParent instance
    """
    self._attr['parent-description'] = Description

    return self

  def SetSiblingsDescription(self, Description):
    """

    Sets the EDXML siblings-description attribute

    Args:
      Description (str): The EDXML siblings-description attribute

    Returns:
      EventTypeParent: The EventTypeParent instance
    """
    self._attr['siblings-description'] = Description

    return self

  def GetEventType(self):
    """

    Returns the name of the parent event type.

    Returns:
      str:
    """
    return self._attr['eventtype']

  def GetPropertyMap(self):
    """

    Returns the property map as a dictionary mapping
    property names of the child event type to property
    names of the parent.

    Returns:
      dict[str,str]:
    """
    return {(Child, Parent) for Mapping in self._attr['propertymap'].split(',') for Child, Parent in Mapping.split(':')}

  def GetParentDescription(self):
    """

    Returns the EDXML 'parent-description' attribute.

    Returns:
      str:
    """
    return self._attr['eventtype']

  def GetSiblingsDescription(self):
    """

    Returns the EDXML 'siblings-description' attribute.

    Returns:
      str:
    """
    return self._attr['eventtype']

  def Validate(self):
    """

    Checks if the event type parent is valid. It only looks
    at the attributes of the definition itself. Since it does
    not have access to the full ontology, the context of
    the parent is not considered. For example, it does not
    check if the parent definition refers to an event type that
    actually exists.

    Raises:
      EDXMLValidationError
    Returns:
      EventTypeParent: The EventTypeParent instance

    """
    if not len(self._attr['eventtype']) <= 40:
      raise EDXMLValidationError(
        'An implicit parent definition refers to a parent event type using an invalid event type name: "%s"' %
        self._attr['eventtype']
      )
    if not re.match(edxml.ontology.EventType.NAME_PATTERN, self._attr['eventtype']):
      raise EDXMLValidationError(
        'An implicit parent definition refers to a parent event type using an invalid event type name: "%s"' %
        self._attr['eventtype']
      )

    if not re.match(self.PROPERTY_MAP_PATTERN, self._attr['propertymap']):
      raise EDXMLValidationError(
        'An implicit parent definition contains an invalid property map: "%s"' % self._attr['propertymap']
      )

    if not 1 <= len(self._attr['parent-description']) <= 128:
      raise EDXMLValidationError(
        'An implicit parent definition contains an parent-description attribute that is either empty or too long: "%s"'
        % self._attr['parent-description']
      )

    if not 1 <= len(self._attr['siblings-description']) <= 128:
      raise EDXMLValidationError(
        'An implicit parent definition contains an siblings-description attribute that is either empty or too long: "%s"'
        % self._attr['siblings-description']
      )

    return self

  def Write(self, Writer):
    """

    Writes the parent into the provided
    EDXMLWriter instance.

    Args:
      Writer (EDXMLWriter): An EDXMLWriter instance

    Returns:
      EventTypeParent: The EventTypeParent instance
    """

    Writer.AddEventTypeParent(self._attr['eventtype'], self._attr['propertymap'], self._attr['parent-description'], self._attr['siblings-description'])

    return self
