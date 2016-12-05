# -*- coding: utf-8 -*-

from collections import MutableMapping
from lxml import etree


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

  def AddParent(self, ParentHash):
    """

    Add the specified sticky hash to the list
    of explicit event parents.

    Args:
      ParentHash (str): Sticky hash, as hexadecimal string

    Returns:
      EDXMLEvent:
    """
    self.Parents.add(ParentHash)
    return self

  def SetParents(self, ParentHashes):
    """

    Replace the set of explicit event parents with the specified
    list of sticky hashes.

    Args:
      ParentHashes (list of str): list of sticky hash, as hexadecimal strings

    Returns:
      EDXMLEvent:
    """
    self.Parents = set(ParentHashes)
    return self

