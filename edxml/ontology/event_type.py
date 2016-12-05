# -*- coding: utf-8 -*-

import re

from edxml.EDXMLBase import EDXMLValidationError

from edxml.EDXMLWriter import EDXMLWriter

class EventType(object):
  """
  Class representing an EDXML event type
  """

  NAME_PATTERN = re.compile("^[a-z0-9-]*$")
  DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
  CLASS_LIST_PATTERN = re.compile("^[a-z0-9, ]*$")
  REPORTER_PLACEHOLDER_PATTERN = re.compile('\\[\\[([^\\]]*)\\]\\]')
  KNOWN_FORMATTERS = ('TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
                      'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'CURRENCY', 'COUNTRYCODE', 'FILESERVER',
                      'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY')

  def __init__(self, Name, DisplayName = None, Description = None, ClassList ='',
               ReporterShort ='no description available', ReporterLong ='no description available', Parent = None):

    self._attr = {
      'name': Name,
      'display-name'   : DisplayName or ' '.join(('%s/%s' % (Name, Name)).split('-')),
      'description'    : Description or Name,
      'classlist'      : ClassList,
      'reporter-short' : ReporterShort,
      'reporter-long'  : ReporterLong
    }

    self._properties = {} # :type Dict[EventProperty]
    self._relations = []  # :type List[PropertyRelation]
    self._parent = Parent # :type EventTypeParent

  @classmethod
  def Create(cls, Name, DisplayNameSingular = None, DisplayNamePlural = None, Description = None):
    """
    
    Creates and returns a new EventType instance. When no display
    names are specified, display names will be created from the
    event type name. If only a singular form is specified, the
    plural form will be auto-generated by appending an 's'.
    
    Args:
      Name (str): Event type name 
      DisplayNameSingular (str): Display name (singular form)
      DisplayNamePlural (str): Display name (plural form)
      Description (str): Event type description

    Returns:
      EventType: The EventType instance
    """
    if DisplayNameSingular:
      DisplayName = '%s/%s' % (DisplayNameSingular, DisplayNamePlural if DisplayNamePlural else '%ss' % DisplayNameSingular)
    else:
      DisplayName = None

    return cls(Name, DisplayName, Description)

  def GetName(self):
    """

    Returns the event type name

    Returns:
      str:
    """
    return self._attr['name']

  def GetDescription(self):
    """

    Returns the event type description

    Returns:
      str:
    """
    return self._attr['description']

  def GetDisplayNameSingular(self):
    """

    Returns the event type display name, in singular form.

    Returns:
      str:
    """
    return self._attr['display-name'].split('/')[0]

  def GetDisplayNamePlural(self):
    """

    Returns the event type display name, in plural form.

    Returns:
      str:
    """
    return self._attr['display-name'].split('/')[1]

  def GetClasses(self):
    """

    Returns the list of classes that this event type
    belongs to.

    Returns:
      list[str]:
    """
    return self._attr['classlist'].split(',')

  def GetProperty(self, PropertyName):
    """

    Returns the property instance of the event type
    property having specified name.

    Returns:
       EventProperty: The EventProperty instance
    """
    return self._properties[PropertyName]

  def GetProperties(self):
    """

    Returns a dictionary containing all properties
    of the event type. The keys in the dictionary
    are the property names, the values are the
    EDXMLProperty instances.

    Returns:
       dict[str,EventProperty]: Properties
    """
    return self._properties

  def GetUniqueProperties(self):
    """

    Returns a dictionary containing all unique properties
    of the event type. The keys in the dictionary
    are the property names, the values are the
    EDXMLProperty instances.

    Returns:
       Dict[str, edxml.ontology.EventProperty]: Properties
    """
    return {n: p for n, p in self._properties.items() if p.IsUnique()}

  def GetPropertyRelations(self):
    """

    Returns the list of property relations that
    are defined in the event type.

    Returns:
      List[edxml.ontology.PropertyRelation]:
    """
    return self._relations

  def HasClass(self, ClassName):
    """

    Returns True if specified class is in the list of
    classes that this event type belongs to, return False
    otherwise.

    Args:
      ClassName (str): The class name

    Returns:
      bool:
    """
    return ClassName in self._attr['classlist'].split(',')

  def IsUnique(self):
    """

    Returns True if the event type is a unique
    event type, returns False otherwise.

    Returns:
      bool:
    """
    for eventProperty in self._properties.values():
      if eventProperty.IsUnique():
        return True

    return False

  def GetReporterShort(self):
    """

    Returns the short reporter string.

    Returns:
      str:
    """
    return self._attr['reporter-short']

  def GetReporterLong(self):
    """

    Returns the long reporter string.

    Returns:
      str:
    """
    return self._attr['reporter-long']

  def GetParent(self):
    """

    Returns the parent event type, or None
    if no parent has been defined.

    Returns:
      EventTypeParent: The parent event type
    """
    return self._parent

  def AddProperty(self, Property):
    """

    Add specified property

    Args:
      Property (EventProperty): EventProperty instance

    Returns:
      EventType: The EventType instance
    """
    self._properties[Property.GetName()] = Property

    return self

  def AddRelation(self, Relation):
    """

    Add specified property relation

    Args:
      Relation (PropertyRelation): Property relation

    Returns:
      EventType: The EventType instance
    """
    self._relations.append(Relation)

    return self

  def SetDescription(self, Description):
    """

    Sets the event type description

    Args:
      Description (str): Description

    Returns:
      EventType: The EventType instance
    """

    self._attr['description'] = str(Description)
    return self

  def SetParent(self, Parent):
    """

    Set the parent event type

    Args:
      Parent (EventTypeParent): Parent event type

    Returns:
      EventType: The EventType instance
    """
    self._parent = Parent

    return self

  def AddClass(self, ClassName):
    """

    Adds the specified event type class

    Args:
      ClassName (str):

    Returns:
      EventType: The EventType instance
    """
    if ClassName:
      if self._attr['classlist'] == '':
        self._attr['classlist'] = ClassName
      else:
        self._attr['classlist'] = ','.join(list(set(self._attr['classlist'].split(',') + [ClassName])))
    return self

  def SetName(self, EventTypeName):
    """

    Sets the name of the event type.

    Args:
     EventTypeName (str): Event type name
    Returns:
      EventType: The EventType instance
    """
    self._attr['name'] = EventTypeName

    return self

  def SetDisplayName(self, Singular, Plural = None):
    """

    Configure the display name. If the plural form
    is omitted, it will be auto-generated by
    appending an 's' to the singular form.

    Args:
      Singular (str): Singular display name
      Plural (str): Plural display name

    Returns:
      EventType: The EventType instance
    """

    if Plural is None:
      Plural = '%ss' % Singular
    self._attr['display-name'] = '%s/%s' % (Singular, Plural)

    return self

  def SetReporterShort(self, Reporter):
    """
    
    Set the short reporter string
    
    Args:
      Reporter (str): The short reporter string 

    Returns:
      EventType: The EventType instance
    """

    if Reporter:
      self._attr['reporter-short'] = Reporter
    return self

  def SetReporterLong(self, Reporter):
    """

    Set the long reporter string

    Args:
      Reporter (str): The long reporter string 

    Returns:
      EventType: The EventType instance
    """

    if Reporter:
      self._attr['reporter-long'] = Reporter
    return self

  def Validate(self):
    """

    Checks if the event type definition is valid. Since it does
    not have access to the full ontology, the context of
    the event type is not considered. For example, it does not
    check if the event type definition refers to a parent event
    type that actually exists. Also, reporter strings are not
    validated.

    Raises:
      EDXMLValidationError
    Returns:
      EventType: The EventType instance

    """
    if not len(self._attr['name']) <= 40:
      raise EDXMLValidationError('The name of event type "%s" is too long.' % self._attr['name'])
    if not re.match(self.NAME_PATTERN, self._attr['name']):
      raise EDXMLValidationError('Event type "%s" has an invalid name.' % self._attr['name'])

    if not len(self._attr['display-name']) <= 64:
      raise EDXMLValidationError(
        'The display name of object type "%s" is too long: "%s"' % (self._attr['name'], self._attr['display-name'])
      )
    if not re.match(self.DISPLAY_NAME_PATTERN, self._attr['display-name']):
      raise EDXMLValidationError(
        'Object type "%s" has an invalid display-name attribute: "%s"' % (self._attr['name'], self._attr['display-name'])
      )

    if not len(self._attr['description']) <= 128:
      raise EDXMLValidationError(
        'The description of object type "%s" is too long: "%s"' % (self._attr['name'], self._attr['description'])
      )

    if not re.match(self.CLASS_LIST_PATTERN, self._attr['classlist']):
      raise EDXMLValidationError(
        'Event type "%s" has an invalid class list: "%s"' %
        (self._attr['name'], self._attr['classlist'])
      )

    for propertyName, eventProperty in self.GetProperties().items():
      eventProperty.Validate()

    for relation in self._relations:
      relation.Validate()

    return self

  @classmethod
  def Read(cls, typeElement):
    eventType = cls(typeElement.attrib['name'], typeElement.attrib['display-name'],
                    typeElement.attrib['description'], typeElement.attrib['classlist'],
                    typeElement.attrib['reporter-short'], typeElement.attrib['reporter-long'])

    for element in typeElement:
      if element.tag == 'parent':
        eventType.SetParent(edxml.ontology.EventTypeParent.Read(element))
      elif element.tag == 'properties':
        for propertyElement in element:
          eventType.AddProperty(edxml.ontology.EventProperty.Read(propertyElement))

      elif element.tag == 'relations':
        for relationElement in element:
          eventType.AddRelation(edxml.ontology.PropertyRelation.Read(relationElement))

    return eventType

  def Update(self, eventType):
    """

    Updates the event type to match the EventType
    instance passed to this method, returning the
    updated instance.

    Args:
      eventType (EventType): The new EventType instance

    Returns:
      EventType: The updated EventType instance

    """
    if self._attr['name'] != eventType.GetName():
      raise Exception('Attempt to update event type "%s" with event type "%s".',
                      (self._attr['name'], eventType.GetName()))

    if self._attr['description'] != eventType.GetDescription():
      raise Exception('Attempt to update event type "%s", but descriptions do not match.',
                      (self._attr['name'], eventType.GetName()))

    if self.GetParent() is not None:
      if eventType.GetParent() is not None:
        self.GetParent().Update(eventType.GetParent())
      else:
        raise Exception('Attempt to update event type "%s", but update does not define a parent.', self._attr['name'])
    else:
      if eventType.GetParent() is not None:
        raise Exception('Attempt to update event type "%s", but update defines a parent.', self._attr['name'])

    updatePropertyNames = set(eventType.GetProperties().keys())
    existingPropertyNames = set(self.GetProperties().keys())

    propertiesAdded = updatePropertyNames - existingPropertyNames
    propertiesRemoved = existingPropertyNames - updatePropertyNames

    if len(propertiesAdded) > 0:
      raise Exception('Event type update added properties.')
    if len(propertiesRemoved) > 0:
      raise Exception('Event type update removed properties.')

    for propertyName, eventProperty in self.GetProperties().items():
      eventProperty.Update(eventType.GetProperty(propertyName))

    self.Validate()

    return self

  def Write(self, Writer):
    """

    Writes the event type into the provided
    EDXMLWriter instance

    Args:
      Writer (EDXMLWriter): EDXMLWriter instance

    Returns:
      EventType: The EventType instance
    """

    Writer.OpenEventDefinition(self._attr['name'], self._attr['description'],self._attr['classlist'],self._attr['reporter-short'], self._attr['reporter-long'],self._attr['display-name'])
    if self._parent:
      self._parent.Write(Writer)
    Writer.OpenEventDefinitionProperties()
    for Property in self._properties.values():
      Property.Write(Writer)
    Writer.CloseEventDefinitionProperties()
    Writer.OpenEventDefinitionRelations()
    for Relation in self._relations:
      Relation.Write(Writer)
    Writer.CloseEventDefinitionRelations()
    Writer.CloseEventDefinition()
    return self

  def GetSingularPropertyNames(self):
    """

    Returns a list of properties that cannot have multiple values.

    Returns:
       list(str): List of property names
    """
    Singular = {}
    for PropertyName, Property in self._properties.items():
      if Property.GetMergeStrategy() in ('match', 'min', 'max', 'increment', 'sum', 'multiply', 'replace'):
        Singular[PropertyName] = True

    if self._parent:
      Singular.update(self._parent.GetPropertyMap())
    return Singular.keys()

  def GetMandatoryPropertyNames(self):
    """

    Returns a list of properties that must have a value

    Returns:
       list(str): List of property names
    """
    Singular = {}
    for PropertyName, Property in self._properties.items():
      if Property.GetMergeStrategy() in ('match', 'min', 'max', 'increment', 'sum', 'multiply'):
        Singular[PropertyName] = True

    return Singular.keys()

  def validateEventStructure(self, edxmlEvent):
    """

    Validates the structure of the event by comparing its
    properties and their object count to the requirements
    of the event type. Generates exceptions that are much
    more readable than standard XML validation exceptions.

    Args:
      edxmlEvent (edxml.EDXMLEvent):
    Raises:
      EDXMLValidationError
    Returns:
      EventType: The EventType instance
    """

    if self.GetParent() is not None:
      ParentPropertyMapping = self.GetParent().GetPropertyMap()
    else:
      ParentPropertyMapping = {}

    for propertyName, objects in edxmlEvent.items():

      if propertyName in ParentPropertyMapping and len(objects) > 0:
          raise EDXMLValidationError(
            ('An event of type %s contains multiple objects of property %s, '
             'but this property can only have one object due to it being used '
             'in an implicit parent definition.') % (self._attr['name'], propertyName)
          )

      # Check if the property is actually
      # supposed to be in this event.
      if propertyName not in self.GetProperties():
        raise EDXMLValidationError(
          ('An event of type %s contains an object of property %s, '
           'but this property does not belong to the event type.') %
          (self._attr['name'], propertyName)
        )

    # Verify that match, min and max properties have an object.
    for PropertyName in self.GetMandatoryPropertyNames():
      if PropertyName not in edxmlEvent:
        raise EDXMLValidationError(
          ('An event of type %s is missing an object for property %s, '
           'while it must have an object due to its configured merge strategy.')
          % (self._attr['name'], PropertyName)
        )

    # Verify that properties that cannot have multiple
    # objects actually have at most one object
    for PropertyName in self.GetSingularPropertyNames():
      if PropertyName in edxmlEvent:
        if len(edxmlEvent[PropertyName]) > 1:
          raise EDXMLValidationError(
            ('An event of type %s has multiple objects of property %s, '
             'while it cannot have more than one due to its configured merge strategy '
             'or due to a implicit parent definition.') %
            (self._attr['name'], PropertyName)
          )

