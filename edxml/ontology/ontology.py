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

  _bricks = {
    'object_types': None,
    'concepts': None
  }  # type: Dict[edxml.ontology.Ontology]

  def __init__(self):
    self._version = 0
    self._event_types = {}    # type: Dict[str, edxml.ontology.EventType]
    self._object_types = {}   # type: Dict[str, edxml.ontology.ObjectType]
    self._sources = {}        # type: Dict[str, edxml.ontology.EventSource]
    self._concepts = {}       # type: Dict[str, edxml.ontology.Concept]

  def GetVersion(self):
    """

    Returns the current ontology version. The initial
    version of a newly created empty ontology is zero.
    On each change, the version is incremented.

    Returns:
      int: Ontology version

    """
    return self._version

  def IsModifiedSince(self, version):
    """

    Returns True if the ontology is newer than
    the specified version. Returns False if the
    ontology version is equal or older.

    Returns:
      bool:

    """
    return self._version > version

  @classmethod
  def RegisterBrick(cls, ontologyBrick):
    """

    Registers an ontology brick with the Ontology class, allowing
    Ontology instances to use any definitions offered by that brick.
    Ontology brick packages expose a register() method, which calls
    this method to register itself with the Ontology class.

    Args:
      ontologyBrick (edxml.ontology.Brick): Ontology brick

    """

    if not cls._bricks['object_types']:
      cls._bricks['object_types'] = edxml.ontology.Ontology()
    if not cls._bricks['concepts']:
      cls._bricks['concepts'] = edxml.ontology.Ontology()

    for _ in ontologyBrick.generateObjectTypes(cls._bricks['object_types']):
      pass

    for _ in ontologyBrick.generateConcepts(cls._bricks['concepts']):
      pass

  def _importObjectTypeFromBrick(self, ObjectTypeName):

    objectType = Ontology._bricks['object_types'].GetObjectType(ObjectTypeName)
    if objectType:
      self._addObjectType(objectType)

  def _importConceptFromBrick(self, ConceptName):

    brickConcept = Ontology._bricks['concepts'].GetConcept(ConceptName)
    if brickConcept:
      self._addConcept(brickConcept)

  def CreateObjectType(self, Name, DisplayNameSingular = None, DisplayNamePlural = None,
                       Description = None, DataType ='string:0:cs:u'):
    """

    Creates and returns a new ObjectType instance. When no display
    names are specified, display names will be created from the
    object type name. If only a singular form is specified, the
    plural form will be auto-generated by appending an 's'.

    If an object type with the same name already exists in the ontology,
    the new definition is ignored and the existing one returned.

    Args:
      Name (str): object type name
      DisplayNameSingular (str): display name (singular form)
      DisplayNamePlural (str): display name (plural form)
      Description (str): short description of the object type
      DataType (str): a valid EDXML data type

    Returns:
      edxml.ontology.ObjectType: The ObjectType instance
    """

    if DisplayNameSingular:
      DisplayName = '%s/%s' % (DisplayNameSingular, DisplayNamePlural if DisplayNamePlural else '%ss' % DisplayNameSingular)
    else:
      DisplayName = None

    if Name not in self._object_types:
      self._object_types[Name] = ObjectType(self, Name, DisplayName, Description, DataType)
      self._childModifiedCallback()

    return self._object_types[Name]

  def CreateConcept(self, Name, DisplayNameSingular = None, DisplayNamePlural = None, Description = None):
    """

    Creates and returns a new Concept instance. When no display
    names are specified, display names will be created from the
    concept name. If only a singular form is specified, the
    plural form will be auto-generated by appending an 's'.

    If a concept with the same name already exists in the ontology,
    the new definition is ignored and the existing one returned.

    Args:
      Name (str): concept name
      DisplayNameSingular (str): display name (singular form)
      DisplayNamePlural (str): display name (plural form)
      Description (str): short description of the concept

    Returns:
      edxml.ontology.Concept: The Concept instance
    """

    if DisplayNameSingular:
      DisplayName = '%s/%s' % (DisplayNameSingular, DisplayNamePlural if DisplayNamePlural else '%ss' % DisplayNameSingular)
    else:
      DisplayName = None

    if Name not in self._concepts:
      self._concepts[Name] = Concept(self, Name, DisplayName, Description)
      self._childModifiedCallback()

    return self._concepts[Name]

  def CreateEventType(self, Name, DisplayNameSingular=None, DisplayNamePlural=None, Description=None):
    """

    Creates and returns a new EventType instance. When no display
    names are specified, display names will be created from the
    event type name. If only a singular form is specified, the
    plural form will be auto-generated by appending an 's'.

    If a concept with the same name already exists in the ontology,
    the new definition is ignored and the existing one returned.

    Args:
      Name (str): Event type name
      DisplayNameSingular (str): Display name (singular form)
      DisplayNamePlural (str): Display name (plural form)
      Description (str): Event type description

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    if DisplayNameSingular:
      DisplayName = '%s/%s' % (DisplayNameSingular, DisplayNamePlural if DisplayNamePlural else '%ss' % DisplayNameSingular)
    else:
      DisplayName = None

    if Name not in self._event_types:
      self._event_types[Name] = EventType(self, Name, DisplayName, Description)
      self._childModifiedCallback()

    return self._event_types[Name]

  def CreateEventSource(self, Uri, Description='no description available', AcquisitionDate='00000000'):
    """

    Creates a new event source definition. If no acquisition date
    is specified, it will be assumed that the acquisition date
    is today.

    If a concept with the same name already exists in the ontology,
    the new definition is ignored and the existing one returned.

    Note:
      Choose your source URIs wisely. The source URIs are used in
      sticky hash computations, so changing the URI may have quite
      a few consequences if the hash is referred to anywhere. Also,
      pay attention to the URI in the context of URIs generated by
      other EDXML data sources, to obtain a consistent, well structured
      source URI tree.

    Args:
     Uri (str): The source URI
     Description (str): Description of the source
     AcquisitionDate (str): Acquisition date in format yyyymmdd

    Returns:
      edxml.ontology.EventSource:
    """

    if Uri not in self._sources:
      self._sources[Uri] = EventSource(self, Uri, Description, AcquisitionDate)
      self._childModifiedCallback()

    return self._sources[Uri]

  def DeleteObjectType(self, objectTypeName):
    """

    Deletes specified object type from the ontology, if
    it exists.

    Warnings:
      Deleting object types may result in an invalid ontology.

    Args:
      objectTypeName (str): An EDXML object type name

    Returns:
      edxml.ontology.Ontology: The ontology
    """

    if objectTypeName in self._object_types:
      del self._object_types[objectTypeName]
      self._childModifiedCallback()

    return self

  def DeleteConcept(self, conceptName):
    """

    Deletes specified concept from the ontology, if
    it exists.

    Warnings:
      Deleting concepts may result in an invalid ontology.

    Args:
      conceptName (str): An EDXML concept name

    Returns:
      edxml.ontology.Ontology: The ontology
    """

    if conceptName in self._concepts:
      del self._concepts[conceptName]
      self._childModifiedCallback()

    return self

  def DeleteEventType(self, eventTypeName):
    """

    Deletes specified event type from the ontology, if
    it exists.

    Warnings:
      Deleting event types may result in an invalid ontology.

    Args:
      eventTypeName (str): An EDXML event type name

    Returns:
      edxml.ontology.Ontology: The ontology
    """

    if eventTypeName in self._event_types:
      del self._event_types[eventTypeName]
      self._childModifiedCallback()

    return self

  def DeleteEventSource(self, sourceUri):
    """

    Deletes specified event source definition from the
    ontology, if it exists.

    Args:
      sourceUri (str): An EDXML event source URI

    Returns:
      edxml.ontology.Ontology: The ontology
    """

    if sourceUri in self._sources:
      del self._sources[sourceUri]
      self._childModifiedCallback()

    return self

  def _childModifiedCallback(self):
    """Callback for change tracking"""
    self._version += 1
    return self

  def _addEventType(self, eventType):
    """

    Adds specified event type to the ontology. If the
    event type exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      eventType (edxml.ontology.EventType): An EventType instance

    Returns:
      edxml.ontology.Ontology: The ontology
    """
    name = eventType.GetName()

    if name in self._event_types:
      self._event_types[name].Update(eventType)
    else:
      self._event_types[name] = eventType.Validate()
      self._childModifiedCallback()

    return self

  def _addObjectType(self, objectType):
    """

    Adds specified object type to the ontology. If the
    object type exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      objectType (edxml.ontology.ObjectType): An ObjectType instance

    Returns:
      edxml.ontology.Ontology: The ontology
    """
    name = objectType.GetName()

    if name in self._object_types:
      self._object_types[name].Update(objectType)
    else:
      self._object_types[name] = objectType.Validate()
      self._childModifiedCallback()

    return self

  def _addConcept(self, concept):
    """

    Adds specified concept to the ontology. If the
    concept exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      concept (edxml.ontology.Concept): A Concept instance

    Returns:
      edxml.ontology.Ontology: The ontology
    """
    name = concept.GetName()

    if name in self._concepts:
      self._concepts[name].Update(concept)
    else:
      self._concepts[name] = concept.Validate()
      self._childModifiedCallback()

    return self

  def _addEventSource(self, eventSource):
    """

    Adds specified event source to the ontology. If the
    event source exists in the ontology, it will be checked
    for consistency with the existing definition.

    Args:
      eventSource (edxml.ontology.EventSource): An EventSource instance

    Returns:
      edxml.ontology.Ontology: The ontology
    """
    uri = eventSource.GetUri()

    if uri in self._sources:
      self._sources[uri].Update(eventSource)
    else:
      self._sources[uri] = eventSource.Validate()
      self._childModifiedCallback()

    return self

  def GetEventTypes(self):
    """

    Returns a dictionary containing all event types
    in the ontology. The keys are the event type
    names, the values are EventType instances.

    Returns:
      Dict[str, edxml.ontology.EventType]: EventType instances
    """
    return self._event_types

  def GetObjectTypes(self):
    """

    Returns a dictionary containing all object types
    in the ontology. The keys are the object type
    names, the values are ObjectType instances.

    Returns:
      Dict[str, edxml.ontology.ObjectType]: ObjectType instances
    """
    return self._object_types

  def GetConcepts(self):
    """

    Returns a dictionary containing all concepts
    in the ontology. The keys are the concept
    names, the values are Concept instances.

    Returns:
      Dict[str, edxml.ontology.Concept]: Concept instances
    """
    return self._concepts

  def GetEventSources(self):
    """

    Returns a dictionary containing all event sources
    in the ontology. The keys are the event source
    URIs, the values are EventSource instances.

    Returns:
      Dict[str, edxml.ontology.EventSource]: EventSource instances
    """
    return self._sources

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

  def GetConceptNames(self):
    """

    Returns the list of names of all defined
    concepts.

    Returns:
       List[str]: List of concept names
    """
    return self._concepts.keys()

  def GetEventType(self, Name):
    """

    Returns the EventType instance having
    specified event type name, or None if
    no event type with that name exists.

    Args:
      Name (str): Event type name

    Returns:
      edxml.ontology.EventType: The event type instance
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
      edxml.ontology.ObjectType: The object type instance
    """
    return self._object_types.get(Name)

  def GetConcept(self, Name):
    """

    Returns the Concept instance having
    specified concept name, or None if
    no concept with that name exists.

    Args:
      Name (str): Concept name

    Returns:
      edxml.ontology.Concept: The Concept instance
    """
    return self._concepts.get(Name)

  def GetEventSource(self, Uri):
    """

    Returns the EventSource instance having
    specified event source URI, or None if
    no event source with that URI exists.

    Args:
      Uri (str): Event source URI

    Returns:
      edxml.ontology.EventSource: The event source instance
    """
    return self._sources.get(Uri)

  def __parseEventTypes(self, eventtypesElement):
    for typeElement in eventtypesElement:
      self._addEventType(EventType.Read(typeElement, self))

  def __parseObjectTypes(self, objecttypesElement):
    for typeElement in objecttypesElement:
      self._addObjectType(
        ObjectType.Read(typeElement, self)
      )

  def __parseConcepts(self, conceptsElement):
    for conceptElement in conceptsElement:
      self._addConcept(
        Concept.Read(conceptElement, self)
      )

  def __parseSources(self, sourcesElement):
    for sourceElement in sourcesElement:
      self._addEventSource(EventSource.Read(sourceElement, self))

  def Validate(self):
    """

    Checks if the defined ontology is a valid EDXML ontology.

    Raises:
      EDXMLValidationError

    Returns:
      edxml.ontology.Ontology: The ontology

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
    for eventTypeName, eventType in self._event_types.iteritems():
      for propertyName, eventProperty in eventType.iteritems():
        objectTypeName = eventProperty.GetObjectTypeName()
        if self.GetObjectType(objectTypeName) is None:
          # Object type is not defined, try to load it from
          # any registered ontology bricks
          self._importObjectTypeFromBrick(objectTypeName)
        if self.GetObjectType(objectTypeName) is None:
          raise EDXMLValidationError(
            'Property "%s" of event type "%s" refers to undefined object type "%s".' %
            (propertyName, eventTypeName, eventProperty.GetObjectTypeName())
          )

    # Check if the concepts referred to by each property exists
    for eventTypeName, eventType in self._event_types.iteritems():
      for propertyName, eventProperty in eventType.iteritems():
        conceptName = eventProperty.GetConceptName()
        if conceptName is not None:
          if self.GetConcept(conceptName) is None:
            # Concept is not defined, try to load it from
            # any registered ontology bricks
            self._importConceptFromBrick(conceptName)
          if self.GetConcept(conceptName) is None:
            raise EDXMLValidationError(
              'Property "%s" of event type "%s" refers to undefined concept "%s".' %
              (propertyName, eventTypeName, eventProperty.GetConceptName())
            )

    # Check if merge strategies make sense for the
    # configured property merge strategies
    for eventTypeName, eventType in self._event_types.iteritems():
      for propertyName, eventProperty in eventType.iteritems():
        if eventProperty.GetMergeStrategy() in ('min', 'max', 'increment', 'sum', 'multiply'):
          if not eventProperty.GetDataType().IsNumerical():
            if eventProperty.GetMergeStrategy() not in ('min', 'max') or not eventProperty.GetDataType().IsDateTime():
              raise EDXMLValidationError(
                  'Property "%s" of event type "%s" has data type %s, which cannot be used with merge strategy %s.'
                  % (propertyName, eventTypeName, eventProperty.GetDataType(), eventProperty.GetMergeStrategy())
              )

    # Check if unique properties have their merge strategies set
    # to 'match'
    # TODO: Still needed for EDXML 3?
    for eventTypeName, eventType in self._event_types.iteritems():
      for propertyName, eventProperty in eventType.iteritems():
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
    for eventTypeName, eventType in self._event_types.iteritems():
      if not eventType.IsUnique():
        for propertyName, eventProperty in eventType.iteritems():
          if eventProperty.GetMergeStrategy() != 'drop':
            raise EDXMLValidationError(
              'Event type "%s" is not unique, but property "%s" has merge strategy %s.' %
              (eventTypeName, propertyName, eventProperty.GetMergeStrategy())
            )

    # Validate event parent definitions
    for eventTypeName, eventType in self._event_types.items():
      if eventType.GetParent() is None:
        continue

      # Check if all unique parent properties are present
      # in the property map
      parentEventType = self.GetEventType(eventType.GetParent().GetEventType())
      for parentPropertyName, parentProperty in parentEventType.iteritems():
        if parentProperty.IsUnique():
          if parentPropertyName not in eventType.GetParent().GetPropertyMap().values():
            raise EDXMLValidationError(
              'Event type %s contains a parent definition which lacks a mapping for unique parent property \'%s\'.' %
              (eventTypeName, parentPropertyName)
            )

      for childProperty, parentProperty in eventType.GetParent().GetPropertyMap().items():

        # Check if child property exists
        if childProperty not in eventType.keys():
          raise EDXMLValidationError(
            'Event type %s contains a parent definition which refers to unknown child property \'%s\'.' %
            (eventTypeName, childProperty)
          )

        # Check if parent property exists and if it is a unique property
        parentEventType = self.GetEventType(eventType.GetParent().GetEventType())
        if parentProperty not in parentEventType.keys() or \
           parentEventType[parentProperty].GetMergeStrategy() != 'match':
          raise EDXMLValidationError(
            ('Event type %s contains a parent definition which refers to parent property "%s" of event type %s, '
             'but this property is not unique, or it does not exist.') %
            (eventTypeName, parentProperty, eventType.GetParent().GetEventType())
          )

        # Check if child property has allowed merge strategy
        if eventType[childProperty].GetMergeStrategy() not in ('match', 'drop'):
          raise EDXMLValidationError(
            ('Event type %s contains a parent definition which refers to child property \'%s\'. '
             'This property has merge strategy %s, which is not allowed for properties that are used in '
             'parent definitions.') %
            (eventTypeName, childProperty, eventType[childProperty].GetMergeStrategy())
          )

    # Verify that inter / intra relations are defined between
    # properties that refer to concepts, in the right way
    for eventTypeName, eventType in self._event_types.items():
      for relation in eventType.GetPropertyRelations():
        if relation.GetTypeClass() in ('inter', 'intra'):
          sourceConcept = eventType[relation.GetSource()].GetConceptName()
          targetConcept = eventType[relation.GetTarget()].GetConceptName()
          if sourceConcept and targetConcept:
            sourcePrimitive = sourceConcept.split('.', 2)[0]
            targetPrimitive = targetConcept.split('.', 2)[0]
            if relation.GetTypeClass() == 'intra':
              if sourcePrimitive != targetPrimitive:
                raise EDXMLValidationError(
                  ('Properties %s and %s in the intra-concept relation in event type %s must both '
                   'refer to the same primitive concept.') %
                  (relation.GetSource(), relation.GetTarget(), eventTypeName)
                )
          else:
            raise EDXMLValidationError(
              ('Both properties %s and %s in the inter/intra-concept relation in event type %s must '
               'refer to a concept.') %
              (relation.GetSource(), relation.GetTarget(), eventTypeName)
            )

    return self

  @classmethod
  def Read(cls, definitionsElement):
    """

    Args:
      definitionsElement (lxml.etree.Element):

    Returns:
      edxml.ontology.Ontology: The ontology
    """

    ontology = cls()

    for element in definitionsElement:
      if element.tag == 'eventtypes':
        ontology.__parseEventTypes(element)
      elif element.tag == 'objecttypes':
        ontology.__parseObjectTypes(element)
      elif element.tag == 'concepts':
        ontology.__parseConcepts(element)
      elif element.tag == 'sources':
        ontology.__parseSources(element)
      else:
        raise TypeError('Unexpected element: "%s"' % element.tag)

    return ontology

  def AddBrick(self, ontologyBrick):
    """
    Updates the ontology using the definitions contained
    in specified ontology brick.

    Args:
      ontologyBrick (edxml.ontology.Brick):

    Returns:
      edxml.ontology.Ontology: The ontology

    """
    ontologyBrick.AddTo(self)

    return self

  def Update(self, otherOntology, validate=True):
    """

    Updates the ontology using the definitions contained
    in another ontology. The other ontology may be specified
    in the form of an Ontology instance or an lxml Element
    containing a full definitions element.

    Args:
      otherOntology (Union[lxml.etree.Element,edxml.ontology.Ontology]):
      validate (bool): Validate the resulting ontology

    Raises;
      EDXMLValidationError

    Returns:
      edxml.ontology.Ontology: The ontology
    """

    if type(otherOntology) == Ontology:
      if validate:
        otherOntology.Validate()
      for ObjectTypeName, objectType in otherOntology.GetObjectTypes().items():
        self._addObjectType(objectType)
      for EventTypeName, eventType in otherOntology.GetEventTypes().items():
        self._addEventType(eventType)
      for ConceptName, concept in otherOntology.GetConcepts().items():
        self._addConcept(concept)
      for uri, source in otherOntology.GetEventSources().items():
        self._addEventSource(source)

    elif isinstance(otherOntology, etree._Element):
      for element in otherOntology:
        if element.tag == 'objecttypes':
          self.__parseObjectTypes(element)
        elif element.tag == 'concepts':
          self.__parseConcepts(element)
        elif element.tag == 'eventtypes':
          self.__parseEventTypes(element)
        elif element.tag == 'sources':
          self.__parseSources(element)
        else:
          raise EDXMLValidationError('Unexpected ontology element: "%s"' % element.tag)

      if validate:
        self.Validate()
    else:
      raise TypeError('Cannot update ontology from %s', str(type(otherOntology)))

    return self

  def GenerateXml(self):
    """

    Generates an lxml etree Element representing
    the EDXML <definitions> tag for this ontology.

    Returns:
      etree.Element: The element

    """
    ontologyElement = etree.Element('definitions')
    objectTypes     = etree.SubElement(ontologyElement, 'objecttypes')
    concepts        = etree.SubElement(ontologyElement, 'concepts')
    eventTypes      = etree.SubElement(ontologyElement, 'eventtypes')
    eventSources    = etree.SubElement(ontologyElement, 'sources')

    for objectTypeName, objectType in self._object_types.iteritems():
      objectTypes.append(objectType.GenerateXml())

    for conceptName, concept in self._concepts.iteritems():
      concepts.append(concept.GenerateXml())

    for eventTypeName, eventType in self._event_types.iteritems():
      eventTypes.append(eventType.GenerateXml())

    for uri, source in self._sources.iteritems():
      eventSources.append(source.GenerateXml())

    return ontologyElement
