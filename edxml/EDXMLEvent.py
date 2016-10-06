# -*- coding: utf-8 -*-

from collections import MutableMapping

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
    may be single values or a list of multiple object values.

    Args:
      Properties (dict(str, list)): Dictionary of properties
      EventTypeName (str, optional): Name of the event type
      SourceUrl (str, optional): Event source URL
      Parents (list, optional): List of parent hashes
      Content (unicode, optional): Event content

    Returns:
      EDXMLEvent
    """
    self.Properties = {Property: Value if type(Value) == list else [Value] for Property, Value in Properties.items()}
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
    return EDXMLEvent(self.Properties.copy(), self.EventTypeName, self.SourceUrl, self.Parents.copy(), self.Content)

  @classmethod
  def Create(cls, Properties, EventTypeName = None, SourceUrl = None, Parents = None, Content = None):
    """

    Creates a new EDXML event.

    Args:
      Properties (dict(str,list)): Dictionary of properties
      EventTypeName (str, optional): Name of the event type
      SourceUrl (str, optional): Event source URL
      Parents (list, optional): List of parent hashes
      Content (unicode, optional): Event content

    Returns:
      EDXMLEvent:
    """
    return cls(Properties, EventTypeName, SourceUrl, Parents, Content)

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
