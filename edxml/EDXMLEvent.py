# -*- coding: utf-8 -*-

import functools
import operator
from collections import MutableMapping
from lxml import etree
from decimal import Decimal

import re


class EDXMLEvent(MutableMapping):
  """Class representing an EDXML event.

  The event allows its properties to be accessed
  and set much like a dictionary:

      Event['property-name'] = 'value'

  Note:
    Properties are lists of object values. On assignment,
    non-list values are automatically wrapped into lists.

  """

  def __init__(self, Properties, EventTypeName = None, SourceUrl = None, Parents = None, Content = None):
    """

    Creates a new EDXML event. The Properties argument must be a
    dictionary mapping property names to object values. Object values
    must be lists of one or multiple object values. Explicit parent
    hashes must be specified as hex encoded strings.

    Args:
      Properties (Dict[str,List[unicode]]): Dictionary of properties
      EventTypeName (Optional[str]): Name of the event type
      SourceUrl (Optional[str]): Event source URL
      Parents (Optional[List[str]]): List of explicit parent hashes
      Content (Optional[unicode]): Event content

    Returns:
      EDXMLEvent
    """
    self.Properties = Properties
    self.EventTypeName = EventTypeName
    self.SourceUrl = SourceUrl
    self.Parents = set(Parents) if Parents is not None else set()
    self.Content = unicode(Content) if Content else u''

  def __str__(self):
    return "\n".join(
      ['%20s:%s' % (Property, ','.join([unicode(Value) for Value in Values])) for Property, Values in self.Properties.iteritems()]
    )

  def __delitem__(self, key):
    self.Properties.pop(key, None)

  def __setitem__(self, key, value):
    if type(value) == list:
      self.Properties[key] = value
    else:
      self.Properties[key] = [value]

  def __len__(self):
    return len(self.Properties)

  def __getitem__(self, key):
    try:
      return self.Properties[key]
    except KeyError:
      return []

  def __contains__(self, key):
    try:
      self.Properties[key][0]
    except (KeyError, IndexError):
      return False
    else:
      return True

  def __iter__(self):
    for PropertyName, Objects in self.Properties.items():
      yield PropertyName

  def copy(self):
    """

    Returns a copy of the event.

    Returns:
       EDXMLEvent
    """
    return EDXMLEvent(self.Properties.copy(), self.EventTypeName, self.SourceUrl, list(self.Parents), self.Content)

  @classmethod
  def Create(cls, Properties, EventTypeName = None, SourceUrl = None, Parents = None, Content = None):
    """

    Creates a new EDXML event. The Properties argument must be a
    dictionary mapping property names to object values. Object values
    may be single values or a list of multiple object values. Explicit parent
    hashes must be specified as hex encoded strings.

    Note:
      For a slight performance gain, use the EDXMLEvent constructor
      directly to create new events.

    Args:
      Properties (Dict[str,Union[unicode,List[unicode]]]): Dictionary of properties
      EventTypeName (Optional[str]): Name of the event type
      SourceUrl (Optional[str]): Event source URL
      Parents (Optional[List[str]]): List of explicit parent hashes
      Content (Optional[unicode]): Event content

    Returns:
      EDXMLEvent:
    """
    return cls(
      {Property: Value if type(Value) == list else [Value] for Property, Value in Properties.items()},
      EventTypeName,
      SourceUrl,
      Parents,
      Content
    )

  def GetTypeName(self):
    """

    Returns the name of the event type.

    Returns:
      str: The event type name

    """
    return self.EventTypeName

  def GetSourceUrl(self):
    """

    Returns the URL of the event source.

    Returns:
      str: The source URL

    """
    return self.SourceUrl

  def GetProperties(self):
    """

    Returns a dictionary containing property names
    as keys. The values are lists of object values.

    Returns:
      Dict[str, List[unicode]]: Event properties

    """
    return self.Properties

  def GetExplicitParents(self):
    """

    Returns a list of sticky hashes of parent
    events. The hashes are hex encoded strings.

    Returns:
      List[str]: List of parent hashes

    """
    return list(self.Parents)

  def GetContent(self):
    """

    Returns the content of the event.

    Returns:
      unicode: Event content

    """
    return self.Content

  @classmethod
  def Read(cls, EventTypeName, SourceUrl, EventElement):
    """

    Creates and returns a new EDXMLEvent instance by reading it from
    specified lxml Element instance.

    Args:
      EventTypeName (str): The name of the event type
      SourceUrl (str): The URL of the EDXML event source
      EventElement (etree.Element): The XML element containing the event

    Returns:
      EDXMLEvent:
    """
    Content = ''
    PropertyObjects = {}
    for element in EventElement:
      if element.tag == 'properties':
        for propertyElement in element:
          PropertyName = propertyElement.tag
          if PropertyName not in PropertyObjects:
            PropertyObjects[PropertyName] = []
          PropertyObjects[PropertyName].append(propertyElement.text)
      elif element.tag == 'content':
        Content = element.text

    return cls(PropertyObjects, EventTypeName, SourceUrl, EventElement.attrib.get('parents'), Content)

  def SetProperties(self, properties):
    """

    Replaces the event properties with the properties
    from specified dictionary. The dictionary must
    contain property names as keys. The values must be
    lists of unicode strings.

    Args:
      properties: Dict(str, List(unicode)): Event properties

    Returns:
      EDXMLEvent:

    """
    self.Properties = properties
    return self

  def CopyPropertiesFrom(self, SourceEvent, PropertyMap):
    """

    Copies properties from another event, mapping property names
    according to specified mapping. The PropertyMap argument is
    a dictionary mapping property names from the source event
    to property names in the target event, which is the event that
    is used to call this method.

    If multiple source properties map to the same target property,
    the objects of both properties will be combined in the target
    property.

    Args:
     SourceEvent (EDXMLEvent):
     PropertyMap (dict(str,str)):

    Returns:
      EDXMLEvent:
    """

    for Source, Targets in PropertyMap.iteritems():
      try:
        SourceProperties = SourceEvent.Properties[Source]
      except KeyError:
        # Source property does not exist.
        continue
      if len(SourceProperties) > 0:
        for Target in (Targets if isinstance(Targets, list) else [Targets]):
          if not Target in self.Properties:
            self.Properties[Target] = []
            self.Properties[Target].extend(SourceProperties)

    return self

  def MovePropertiesFrom(self, SourceEvent, PropertyMap):
    """

    Moves properties from another event, mapping property names
    according to specified mapping. The PropertyMap argument is
    a dictionary mapping property names from the source event
    to property names in the target event, which is the event that
    is used to call this method.

    If multiple source properties map to the same target property,
    the objects of both properties will be combined in the target
    property.

    Args:
     SourceEvent (EDXMLEvent):
     PropertyMap (dict(str,str)):

    Returns:
      EDXMLEvent:
    """

    for Source, Targets in PropertyMap.iteritems():
      try:
        for Target in (Targets if isinstance(Targets, list) else [Targets]):
          if not Target in self.Properties:
            self.Properties[Target] = []
          self.Properties[Target].extend(SourceEvent.Properties[Source])
      except KeyError:
        # Source property does not exist.
        pass
      else:
        del SourceEvent.Properties[Source]

    return self

  def SetType(self, EventTypeName):
    """

    Set the event type.

    Args:
      EventTypeName (str): Name of the event type

    Returns:
      EDXMLEvent:
    """
    self.EventTypeName = EventTypeName
    return self

  def SetContent(self, Content):
    """

    Set the event content.

    Args:
      Content (unicode): Content string

    Returns:
      EDXMLEvent:
    """
    self.Content = Content
    return self

  def SetSource(self, SourceUrl):
    """

    Set the event source.

    Args:
      SourceUrl (str): EDXML source URL

    Returns:
      EDXMLEvent:
    """
    self.SourceUrl = SourceUrl
    return self

  def AddParents(self, ParentHashes):
    """

    Add the specified sticky hashes to the list
    of explicit event parents.

    Args:
      ParentHashes (List[str]): list of sticky hash, as hexadecimal strings

    Returns:
      EDXMLEvent:
    """
    self.Parents.update(ParentHashes)
    return self

  def SetParents(self, ParentHashes):
    """

    Replace the set of explicit event parents with the specified
    list of sticky hashes.

    Args:
      ParentHashes (List[str]): list of sticky hash, as hexadecimal strings

    Returns:
      EDXMLEvent:
    """
    self.Parents = set(ParentHashes)
    return self

  def MergeWith(self, collidingEvents, edxmlOntology):
    """
    Merges the event with event data from a number of colliding
    events. It returns True when the event was updated
    as a result of the merge, returns False otherwise.

    Args:
      collidingEvents (List[EDXMLEvent]): Iterable yielding events
      edxmlOntology (edxml.ontology.Ontology): The EDXML ontology

    Returns:
      bool: Event was changed or not

    """

    eventType = edxmlOntology.GetEventType(self.EventTypeName)
    properties = eventType.GetProperties()
    propertyNames = properties.keys()
    uniqueProperties = eventType.GetUniqueProperties()

    if len(uniqueProperties) == 0:
      raise TypeError("MergeEvent was called for event type %s, which is not a unique event type." % self.EventTypeName)

    EventObjectsA = self.GetProperties()

    # Below, we initialize three dictionaries containing
    # event object sets. All objects are complete, in the
    # sense that they contain a list of objects for each
    # of the defined properties of the event type, even
    # if the event has no objects for the property.
    #
    # The Original dict holds the original event, before
    # the merge.
    # The Target dict is what will eventually become the
    # new, merged event.
    # The source event holds all object values from all
    # source events.

    Original = {}
    Source = {}
    Target = {}

    for PropertyName in propertyNames:
      if PropertyName in EventObjectsA:
        Original[PropertyName] = set(EventObjectsA[PropertyName])
        Target[PropertyName] = set(EventObjectsA[PropertyName])
      else:
        Original[PropertyName] = set()
        Target[PropertyName] = set()
      Source[PropertyName] = set()

    for event in collidingEvents:
      EventObjectsB = event.GetProperties()
      for PropertyName in propertyNames:
        if PropertyName in EventObjectsB:
          Source[PropertyName].update(EventObjectsB[PropertyName])

    # Now we update the objects in Target
    # using the values in Source
    for PropertyName in Source:

      if PropertyName in uniqueProperties:
        # Unique property, does not need to be merged.
        continue

      MergeStrategy = properties[PropertyName].GetMergeStrategy()

      if MergeStrategy in ('min', 'max', 'increment', 'sum', 'multiply'):
        # We have a merge strategy that requires us to cast
        # the object values into numbers.
        SplitDataType = properties[PropertyName].GetDataType(edxmlOntology).GetSplit()
        if SplitDataType[0] in ('number', 'timestamp'):
          if MergeStrategy in ('min', 'max'):
            Values = set()
            if SplitDataType[0] == 'timestamp':
              Values.update(Decimal(Value) for Value in Source[PropertyName])
              Values.update(Decimal(Value) for Value in Target[PropertyName])
            else:
              if SplitDataType[1] in ('float', 'double'):
                Values.update(float(Value) for Value in Source[PropertyName])
                Values.update(float(Value) for Value in Target[PropertyName])
              elif SplitDataType[1] == 'decimal':
                Values.update(Decimal(Value) for Value in Source[PropertyName])
                Values.update(Decimal(Value) for Value in Target[PropertyName])
              elif SplitDataType[1] != 'hex':
                Values.update(int(Value) for Value in Source[PropertyName])
                Values.update(int(Value) for Value in Target[PropertyName])

            if MergeStrategy == 'min':
              Target[PropertyName] = {str(min(Values))}
            else:
              Target[PropertyName] = {str(max(Values))}

          elif MergeStrategy == 'increment':
            if SplitDataType[0] == 'timestamp':
              Target[PropertyName] = {'%.6f' % Decimal(next(iter(Target[PropertyName]))) + Decimal(len(Source[PropertyName]))}
            else:
              if SplitDataType[1] in ('float', 'double'):
                Target[PropertyName] = {str(float(next(iter(Target[PropertyName]))) + len(collidingEvents))}
              elif SplitDataType[1] == 'decimal':
                Target[PropertyName] = {str(Decimal(next(iter(Target[PropertyName]))) + len(collidingEvents))}
              elif SplitDataType[1] != 'hex':
                Target[PropertyName] = {str(int(next(iter(Target[PropertyName]))) + len(collidingEvents))}

          elif MergeStrategy == 'sum':
            if SplitDataType[0] == 'timestamp':
              Target[PropertyName] = {
                '%.6f' % Decimal(next(iter(Target[PropertyName]))) + sum(Decimal(Value) for Value in Source[PropertyName])
              }
            # When hex is not in number family anymore, replace the below line with elif SplitDataType[0] == 'number':
            else:
              if SplitDataType[1] in ['float', 'double']:
                Target[PropertyName] = {
                  str(float(next(iter(Target[PropertyName]))) + sum(float(Value) for Value in Source[PropertyName]))
                }
              elif SplitDataType[1] == 'decimal':
                Target[PropertyName] = {
                  str(Decimal(next(iter(Target[PropertyName]))) + sum(Decimal(Value) for Value in Source[PropertyName]))
                }
              elif SplitDataType[1] != 'hex':
                Target[PropertyName] = {
                  str(int(next(iter(Target[PropertyName]))) + sum(int(Value) for Value in Source[PropertyName]))
                }

          elif MergeStrategy == 'multiply':
            if SplitDataType[0] == 'timestamp':
              Target[PropertyName] = {
                '%.6f' % functools.reduce(
                  operator.mul, [Decimal(Value) for Value in Target[PropertyName]], Decimal(next(iter(Source[PropertyName])))
                )
              }
            else:
              if SplitDataType[1] in ('float', 'double'):
                Target[PropertyName] = {
                  str(functools.reduce(
                    operator.mul, [float(Value) for Value in Target[PropertyName]], float(next(iter(Source[PropertyName]))))
                  )
                }
              elif SplitDataType[1] == 'decimal':
                sourceValue = Decimal(next(iter(Source[PropertyName])))
                Target[PropertyName] = {
                  str(functools.reduce(
                    operator.mul, [Decimal(Value) for Value in Target[PropertyName]], sourceValue
                  ).quantize(sourceValue))
                }
              elif SplitDataType[1] != 'hex':
                Target[PropertyName] = {
                  str(functools.reduce(
                    operator.mul, [int(Value) for Value in Target[PropertyName]], int(next(iter(Source[PropertyName]))))
                  )
                }

      elif MergeStrategy == 'add':
        Target[PropertyName].update(Source[PropertyName])

      elif MergeStrategy == 'replace':
        Target[PropertyName] = set(collidingEvents[-1].get(PropertyName, []))

    SourceParents = set(parent for sourceEvent in collidingEvents for parent in sourceEvent.GetExplicitParents())

    # Merge the explicit event parents
    if len(SourceParents) > 0:
      OriginalParents = self.GetExplicitParents()
      self.SetParents(self.GetExplicitParents() + list(SourceParents))
    else:
      OriginalParents = set()

    # Determine if anything changed
    EventUpdated = False
    for PropertyName in propertyNames:
      if PropertyName not in Original and len(Target[PropertyName]) > 0:
        EventUpdated = True
        break
      if Target[PropertyName] != Original[PropertyName]:
        EventUpdated = True
        break

    if not EventUpdated:
      if len(SourceParents) > 0:
        if OriginalParents != SourceParents:
          EventUpdated = True

    # Modify event if needed
    if EventUpdated:
      self.SetProperties(Target)
      return True
    else:
      return False

