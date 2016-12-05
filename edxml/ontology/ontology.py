# -*- coding: utf-8 -*-
from lxml import etree

from typing import Dict

import edxml.ontology
from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import *


class Ontology(object):
  """
  Class representing an EDXML ontology
  """

  def __init__(self):
    self._event_types = {}    # type: Dict[str, edxml.ontology.EventType]
    self._object_types = {}   # type: Dict[str, edxml.ontology.ObjectType]
    self._sources = {}        # type: Dict[str, edxml.ontology.EventSource]

  def AddEventType(self, eventType):
    """

    Adds specified event type to the ontology. If the
    event type exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      eventType (EventType): An EventType instance
    Returns:
      Ontology: The ontology
    """
    name = eventType.GetName()

    if name in self._event_types:
      self._event_types[name].Update(eventType)
    else:
      self._event_types[name] = eventType.Validate()

    return self

  def AddObjectType(self, objectType):
    """

    Adds specified object type to the ontology. If the
    object type exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      objectType (ObjectType): An ObjectType instance
    Returns:
      Ontology: The ontology
    """
    name = objectType.GetName()

    if name in self._object_types:
      self._object_types[name].Update(objectType)
    else:
      self._object_types[name] = objectType.Validate()

    return self

  def AddEventSource(self, eventSource):
    """

    Adds specified event source to the ontology. If the
    event source exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      eventSource (EventSource): An EventSource instance
    Returns:
      Ontology: The ontology
    """
    url = eventSource.GetUrl()

    if url in self._sources:
      self._sources[url].Update(eventSource)
    else:
      self._sources[url] = eventSource.Validate()

    return self

  def GenerateEventTypes(self):
    """

    Generates all event types in the ontology as
    dictionary elements. The keys are the event type
    names, the values are EventType instances.

    Yields:
      EventType: EventType instance
    """
    for name, eventType in self._event_types.items():
      yield name, eventType

  def GenerateObjectTypes(self):
    """

    Generates all object types in the ontology as
    dictionary elements. The keys are the object type
    names, the values are ObjectType instances.

    Yields:
      ObjectType: ObjectType instance
    """
    for name, objectType in self._object_types.items():
      yield name, objectType

  def GenerateEventSources(self):
    """

    Generates all event sources in the ontology as
    dictionary elements. The keys are the event source
    URLs, the values are EventSource instances.

    Yields:
      EventSource: EventSource instance
    """
    for url, eventSource in self._sources.items():
      yield url, eventSource

  def GetEventTypeNames(self):
    """

    Returns the list of names of all defined
    event types.

    Returns:
       List[str]: List of event type names
    """
    return self._event_types.keys()

  def GetObjectTypeNames(self):
    """

    Returns the list of names of all defined
    object types.

    Returns:
       List[str]: List of object type names
    """
    return self._object_types.keys()

  def GetEventType(self, Name):
    """

    Returns the EventType instance having
    specified event type name, or None if
    no event type with that name exists.

    Args:
      Name (str): Event type name
    Returns:
      EventType: The event type instance
    """
    return self._event_types.get(Name)

  def GetObjectType(self, Name):
    """

    Returns the ObjectType instance having
    specified object type name, or None if
    no object type with that name exists.

    Args:
      Name (str): Object type name
    Returns:
      ObjectType: The object type instance
    """
    return self._object_types.get(Name)

  def GetEventSource(self, Url):
    """

    Returns the EventSource instance having
    specified event source URL, or None if
    no event source with that URL exists.

    Args:
      Url (str): Event source URL
    Returns:
      EventSource: The event source instance
    """
    return self._sources.get(Url)

  def GetEventSourceById(self, Id):
    # TODO: Remove this method as soon as the event-id
    # attribute is gone.
    for sourceUrl, source in self._sources.items():
      if source.GetId() == Id:
        return source

  def __parseEventTypes(self, eventtypesElement):
    for typeElement in eventtypesElement:
      self.AddEventType(EventType.Read(typeElement))

  def __parseObjectTypes(self, objecttypesElement):
    for typeElement in objecttypesElement:
      self.AddObjectType(
        ObjectType.Read(typeElement)
      )

  def __parseSources(self, sourcesElement):
    for sourceElement in sourcesElement:
      self.AddEventSource(EventSource.Read(sourceElement))

  def Validate(self):
    """

    Checks if the defined ontology is a valid EDXML ontology.

    Raises:
      EDXMLValidationError
    Returns:
      Ontology: The ontology

    """
    # Validate all object types
    for objectTypeName, objectType in self._object_types.items():
      objectType.Validate()

    # Validate all event types and their
    # reporter strings
    for eventTypeName, eventType in self._event_types.items():
      eventType.Validate()
      eventType.ValidateReporterString(eventType.GetReporterShort(), self)
      eventType.ValidateReporterString(eventType.GetReporterLong(), self)

    # Check if all event type parents are defined
    for eventTypeName, eventType in self._event_types.items():
      eventType.Validate()
      if eventType.GetParent() is not None:
        if eventType.GetParent().GetEventType() not in self._event_types:
          raise EDXMLValidationError('Event type "%s" refers to parent event type "%s", which is not defined.' %
                                     (eventTypeName, eventType.GetParent().GetEventType()))

    # Check if the object type of each property exists
    for eventTypeName, eventType in self._event_types.items():
      for propertyName, eventProperty in eventType.GetProperties().items():
        if self.GetObjectType(eventProperty.GetObjectTypeName()) is None:
          raise EDXMLValidationError(
            'Property "%s" of event type "%s" refers to undefined object type "%s".' %
            (propertyName, eventTypeName, eventProperty.GetObjectTypeName())
          )

    # Check if merge strategies make sense for the
    # configured property merge strategies
    for eventTypeName, eventType in self._event_types.items():
      for propertyName, eventProperty in eventType.GetProperties().items():
        if eventProperty.GetMergeStrategy() in ('min', 'max', 'increment', 'sum', 'multiply'):
          dataType = self.GetObjectType(eventProperty.GetObjectTypeName()).GetDataType()
          if not DataType(dataType).IsNumerical():
            raise EDXMLValidationError(
              ('Property "%s" of event type "%s" with merge strategy min, max, increment, sum or multiply '
               'must be a number or timestamp.') % (propertyName, eventTypeName)
            )

    # Check if unique properties have their merge strategies set
    # to 'match'
    # TODO: Still needed for EDXML 3?
    for eventTypeName, eventType in self._event_types.items():
      for propertyName, eventProperty in eventType.GetProperties().items():
        if eventProperty.IsUnique():
          if eventProperty.GetMergeStrategy() != 'match':
            raise EDXMLValidationError(
              'Unique property "%s" of event type "%s" does not have its merge strategy set to "match".' %
              (propertyName, eventTypeName)
            )
        else:
          if eventProperty.GetMergeStrategy() == 'match':
            raise EDXMLValidationError(
              'Property "%s" of event type "%s" is not unique but it does have its merge strategy set to "match".' %
              (propertyName, eventTypeName)
            )

    # Verify that non-unique event type only have
    # properties with merge strategy 'drop'.
    for eventTypeName, eventType in self._event_types.items():
      if not eventType.IsUnique():
        for propertyName, eventProperty in eventType.GetProperties().items():
          if eventProperty.GetMergeStrategy() != 'drop':
            raise EDXMLValidationError(
              'Event type "%s" is not unique, but property "%s" has merge strategy %s.' %
              (eventTypeName, propertyName, eventProperty.GetMergeStrategy())
            )

    # Check if properties in property relations are defined
    for eventTypeName, eventType in self._event_types.items():
      for relation in eventType.GetPropertyRelations():
        if relation.GetSource() not in eventType.GetProperties().keys():
          raise EDXMLValidationError(
            'Event type "%s" contains a property relation referring to property "%s", which is not defined.' %
            (eventTypeName, relation.GetSource()))
        if relation.GetDest() not in eventType.GetProperties().keys():
          raise EDXMLValidationError(
            'Event type "%s" contains a property relation referring to property "%s", which is not defined.' %
            (eventTypeName, relation.GetDest()))

    # Validate event parent definitions
    for eventTypeName, eventType in self._event_types.items():
      if eventType.GetParent() is None:
        continue

      # Check if all unique parent properties are present
      # in the property map
      parentEventType = self.GetEventType(eventType.GetParent().GetEventType())
      for parentPropertyName, parentProperty in parentEventType.GetProperties().items():
        if parentProperty.IsUnique():
          if parentPropertyName not in eventType.GetParent().GetPropertyMap().values():
            raise EDXMLValidationError(
              'Event type %s contains a parent definition which lacks a mapping for unique parent property \'%s\'.' %
              (eventTypeName, parentPropertyName)
            )

      for childProperty, parentProperty in eventType.GetParent().GetPropertyMap().items():

        # Check if child property exists
        if childProperty not in eventType.GetProperties().keys():
          raise EDXMLValidationError(
            'Event type %s contains a parent definition which refers to unknown child property \'%s\'.' %
            (eventTypeName, childProperty)
          )

        # Check if parent property exists and if it is a unique property
        parentEventType = self.GetEventType(eventType.GetParent().GetEventType())
        if parentProperty not in parentEventType.GetProperties().keys() or \
           parentEventType.GetProperty(parentProperty).GetMergeStrategy() != 'match':
          raise EDXMLValidationError(
            ('Event type %s contains a parent definition which refers to parent property "%s" of event type %s, '
             'but this property is not unique, or it does not exist.') %
            (eventTypeName, parentProperty, eventType.GetParent().GetEventType())
          )

        # Check if child property has allowed merge strategy
        if eventType.GetProperty(childProperty).GetMergeStrategy() not in ('match', 'drop'):
          raise EDXMLValidationError(
            ('Event type %s contains a parent definition which refers to child property \'%s\'. '
             'This property has merge strategy %s, which is not allowed for properties that are used in '
             'parent definitions.') %
            (eventTypeName, childProperty, eventType.GetProperty(childProperty).GetMergeStrategy())
          )

    return self

  @classmethod
  def Read(cls, definitionsElement):
    """

    Args:
      definitionsElement (lxml.etree.Element):

    Returns:
      Ontology: The ontology
    """

    ontology = cls()

    for element in definitionsElement:
      if element.tag == 'eventtypes':
        ontology.__parseEventTypes(element)
      elif element.tag == 'objecttypes':
        ontology.__parseObjectTypes(element)
      elif element.tag == 'sources':
        ontology.__parseSources(element)
      else:
        raise TypeError('Unexpected element: "%s"' % element.tag)

    return ontology

  def Update(self, otherOntology):
    """

    Updates the ontology using the definitions contained
    in another ontology. The other ontology may be specified
    in the form of an Ontology instance or an lxml Element
    containing a full definitions element.

    Args:
      otherOntology (Union[lxml.etree.Element,Ontology]):

    Returns:
      Ontology: The ontology
    """

    if type(otherOntology) == Ontology:
      for ObjectTypeName, objectType in otherOntology.GenerateObjectTypes():
        self.AddObjectType(objectType)
      for EventTypeName, eventType in otherOntology.GenerateEventTypes():
        self.AddEventType(eventType)
      for Url, source in otherOntology.GenerateEventSources():
        self.AddEventSource(source)

    elif isinstance(otherOntology, etree._Element):
      for element in otherOntology:
        if element.tag == 'eventtypes':
          self.__parseEventTypes(element)
        elif element.tag == 'objecttypes':
          self.__parseObjectTypes(element)
        elif element.tag == 'sources':
          self.__parseSources(element)
        else:
          raise TypeError('Unexpected element: "%s"' % element.tag)

      self.Validate()
    else:
      raise TypeError('Cannot update ontology from %s', str(type(otherOntology)))

    return self

  def Write(self, Writer):
    """

    Writes the ontology into the provided
    EDXMLWriter instance

    Args:
      Writer (EDXMLWriter): EDXMLWriter instance

    Returns:
      Ontology: The ontology
    """

    RequiredObjectTypes = []
    Writer.OpenDefinitions()

    Writer.OpenEventDefinitions()
    for eventType in self._event_types.values():
      eventType.Write(Writer)
      for Property in eventType.GetProperties().values():
        RequiredObjectTypes.append(Property.GetObjectTypeName())
    Writer.CloseEventDefinitions()
    Writer.OpenObjectTypes()
    for objectType in self._object_types.values():
      if objectType.GetName() in RequiredObjectTypes:
        objectType.Write(Writer)
    Writer.CloseObjectTypes()
    Writer.OpenSourceDefinitions()
    for eventSource in self._sources.values():
      eventSource.Write(Writer)
    Writer.CloseSourceDefinitions()
    Writer.CloseDefinitions()

    return self