# -*- coding: utf-8 -*-
import time

from edxml.EDXMLWriter import EDXMLWriter
from edxml.EDXMLBase import EDXMLError
from edxml.EDXMLEvent import EDXMLEvent

class SimpleEDXMLWriter(object):
  """High level EDXML stream writer

  This class offers a simplified interface to
  the EDXMLWriter class. Apart from a simplified
  interface, it implements some additional features
  like buffering, post-processing, automatic merging
  of output events and latency control.

  """

  def __init__(self, Output, Validate = True, ValidateObjects = True):
    """

    Create a new SimpleEDXMLWriter, outputting
    an EDXML stream to specified output.

    By default, the output will be fully validated.
    Optionally, validating the event objects can
    be disabled, or output validation can be completely
    disabled by setting Validate to True. This may be
    used to boost performance in case you know that
    the data will be validated at the receiving end,
    or in case you know that your generator is perfect. :)

    The Output parameter is a file-like object
    that will be used to send the XML data to.
    This file-like object can be pretty much
    anything, as long as it has a write() method.

    Args:
     Output (file): a file-like object
     Validate (bool`, optional): Validate the output (True) or not (False)
     ValidateObjects (bool`, optional): Validate event objects (True) or not (False)

    Returns:
       SimpleEDXMLWriter:
    """

    self._buffer_size = 1024
    self._max_latency = 0
    self._last_write_time = time.time()
    self._writing_events = False
    self._ignore_invalid_objects = False
    self._ignore_invalid_events = False
    self._log_invalid_events = False
    self._current_source_id = None
    self._current_event_type = None
    self._current_event_group_source = None
    self._current_event_group_type = None
    self._event_buffers = {}
    self._event_types = {}  # :type: Dict[EventType]
    self._event_type_postprocessors = {}
    self._automerge = {}
    self._object_types = {}
    self._sources = {}  # :type: Dict[EventSource]
    self._source_ids = {}
    self._writer = EDXMLWriter(Output, Validate, ValidateObjects)

  def _write_ontology(self):

    RequiredObjectTypes = []
    self._writer.OpenDefinitions()

    self._writer.OpenEventDefinitions()
    for EventType in self._event_types.values():
      EventType.Write(self._writer)
      for Property in EventType.GetProperties().values():
        RequiredObjectTypes.append(Property.GetObjectTypeName())
    self._writer.CloseEventDefinitions()
    self._writer.OpenObjectTypes()
    for ObjectType in self._object_types.values():
      if ObjectType.GetName() in RequiredObjectTypes:
        ObjectType.Write(self._writer)
    self._writer.CloseObjectTypes()
    self._writer.OpenSourceDefinitions()
    for EventSource in self._sources.values():
      EventSource.Write(self._writer)
    self._writer.CloseSourceDefinitions()
    self._writer.CloseDefinitions()

  def RegisterEventPostProcessor(self, EventTypeName, Callback):
    """

    Register a post-processor for events of specified type. Whenever
    an event is submitted through the AddEvent() method, the supplied
    callback method will be invoked before the event is output. The
    callback must have the the same call signature as the AddEvent()
    method. The two optional arguments Type and Source will always
    be specified when the callback is invoked. The callback should
    not return anything.

    Apart from generating events, callbacks can also modify the event
    that is about to be outputted, by editing its call arguments.

    Args:
      EventTypeName (str): Name of the event type
      Callback (callable): The callback

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """

    if not EventTypeName in self._event_type_postprocessors:
      self._event_type_postprocessors[EventTypeName] = Callback
    else:
      raise Exception('Another post processor has already been registered for %s.' % EventTypeName)

    return self

  def IgnoreInvalidObjects(self):
    """

    Instructs the EDXML writer to ignore invalid object
    values. After calling this method, any event value
    that fails to validate will be silently dropped.

    Note:
      Dropping object values may lead to invalid events.

    Note:
      This has no effect when object validation is disabled.

    Returns:
       SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._ignore_invalid_objects = True

    return self

  def IgnoreInvalidEvents(self, Warn = False):
    """

    Instructs the EDXML writer to ignore invalid events.
    After calling this method, any event that fails to
    validate will be dropped. If Warn is set to True,
    a detailed warning will be printed, allowing the
    source and cause of the problem to be determined.

    Note:
      This also implies that invalid objects will be
      ignored.

    Note:
      This has no effect when event validation is disabled.

    Args:
      Warn (bool`, optional): Print warnings or not

    Returns:
       SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._ignore_invalid_objects = True
    self._ignore_invalid_events = True
    self._log_invalid_events = Warn

    return self

  def AutoMerge(self, EventTypeName):
    """

    Enable auto-merging for events of specified event
    type. Auto-merging implies that colliding output events
    will be merged before outputting them. This may be useful
    to reduce the event output rate when generating large
    numbers of colliding events.

    Args:
      EventTypeName (str): The name of the event type

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._automerge[EventTypeName] = True

    return self

  def AddEventType(self, Type):
    """

    Add specified event type to the output stream.

    Args:
      Type (EventType): EventType instance

    Returns:
     SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    if self._writing_events:
      raise EDXMLError('You cannot add ontology elements after writing the first event.')

    self._event_types[Type.GetName()] = Type
    return self

  def AddObjectType(self, Type):
    """

    Add specified object type to the output stream.

    Args:
      Type (ObjectType): ObjectType instance

    Returns:
     SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    if self._writing_events:
      raise EDXMLError('You cannot add ontology elements after writing the first event.')

    self._object_types[Type.GetName()] = Type
    return self

  def AddEventSource(self, Source):
    """

    Add specified event source to the output stream.

    Args:
      Source (EventSource): EventSource instance

    Returns:
     SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._sources[Source.GetId()] = Source
    self._source_ids[Source.GetUrl()] = Source.GetId()
    return self

  def _get_normalized_event_objects(self, EventTypeName, Properties):

    Normalized = []

    for Property, Objects in Properties.items():
      ObjectTypeName = self._writer.EDXMLParser.Definitions.GetPropertyObjectType(EventTypeName, Property)
      DataType = self._writer.EDXMLParser.Definitions.GetObjectTypeDataType(ObjectTypeName)
      for Object in Objects:
        Normalized.append({
          'property': Property,
          'value':    self._writer.EDXMLParser.NormalizeObject(Object, DataType)
        })

    return Normalized

  def SetEventType(self, EventTypeName):
    """

    Set the default output event type. If no explicit event type
    is used in calls to AddEvent(), the default event type will
    be used.

    Args:
      EventTypeName (str): The event type name

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._current_event_type = EventTypeName

    return self

  def SetEventSource(self, SourceId):
    """

    Set the default event source for the output events. If no explicit
    source is specified in calls to AddEvent(), the default source will
    be used.

    Args:
      SourceId (str): The event source identifier

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._current_source_id = SourceId

    return self

  def AddEvent(self, Event):
    """

    Add the specified event to the output stream. If the event type or
    event source are not specified, the default type and source that
    have been set using SetEventType() and SetEventSource() will be used.

    Args:
      Event (EDXMLEvent): An EDXMLEvent instance

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance

    """

    return self.GenerateEvent(
      Event.Properties,
      Event.Content,
      Event.Parents,
      Event.EventTypeName,
      self._source_ids.get(Event.SourceUrl)
    )

  def GenerateEvent(self, Properties, Content='', Parents=None, Type=None, Source=None):
    """

    Generate a new event and write to the output stream. If the event type or
    event source are not specified, the default type and source that
    have been set using SetEventType() and SetEventSource() will be used.

    The Properties dictionary must have keys containing the property names. The values
    of the dictionary must be object values or lists of object values. Object values
    can be anything can be cast to a unicode object.

    Args:
      Properties (dict[str]): The event properties
      Content (str): Event content string
      Parents (list[str], Optional): List of sticky hashes, as hex strings
      Type (str, Optional): Event type name
      Source (str, Optional): Source identifier

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """

    EventSourceId = self._sources[Source].GetId() if Source is not None else self._current_source_id
    EventTypeName = Type if Type is not None else self._current_event_type

    if EventSourceId is None:
      if len(self._sources) == 1:
        EventSourceId = self._sources.itervalues().next().GetId()
      else:
        raise EDXMLError('No event source was specified.')

    if EventTypeName is None:
      if len(self._event_types) == 1:
        EventTypeName = self._event_types.itervalues().next().GetName()
      else:
        raise EDXMLError('No event type was specified.')

    # Convert the property objects to lists, in case they aren't
    Properties = {PropertyName: (Values if type(Values) == list else [Values]) for PropertyName, Values in Properties.items()}

    if EventTypeName in self._event_type_postprocessors:
      self._event_type_postprocessors[EventTypeName](Properties, Content, Parents, EventTypeName, EventSourceId)

    EventGroup = '%s:%s' % (EventTypeName, EventSourceId)
    if not EventGroup in self._event_buffers:
      self._event_buffers[EventGroup] = {True: {}, False: []}

    if not self._writing_events:
      self._write_ontology()
      self._writer.OpenEventGroups()
      self._writing_events = True

    Merge = EventTypeName in self._automerge
    if Merge:
      # We need to compute the sticky hash, check
      # for collisions and merge if needed.
      Hash = self._writer.EDXMLParser.Definitions.ComputeStickyHash(
        EventTypeName,
        self._get_normalized_event_objects(Type, Properties),
        Content
      )

      if not Hash in self._event_buffers[EventGroup][Merge]:
        self._event_buffers[EventGroup][Merge][Hash] = [Properties, Content, Parents]
      else:
        self._writer.EDXMLParser.Definitions.MergeEvents(
          EventTypeName,
          self._event_buffers[EventGroup][Merge][Hash][0], Properties)
    else:
      self._event_buffers[EventGroup][Merge].append([Properties, Content, Parents])

    if len(self._event_buffers[EventGroup][Merge]) > self._buffer_size or \
          0 < self._max_latency <= (time.time() - self._last_write_time):
      self._flush_buffer(EventTypeName, EventSourceId, EventGroup, Merge)

    return self

  def SetBufferSize(self, EventCount):
    """

    Sets the buffer size for writing events to
    the output. The default buffer size is 1024
    events.

    Args:
     EventCount (int): Maximum number of events

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._buffer_size = EventCount
    return self

  def SetOutputLatency(self, Latency):
    """

    Sets the output latency, in seconds. Setting this
    value to a positive value forces the writer to
    flush its buffers at least once every time the
    latency time expires. The default latency is zero,
    which means that output will be silent for as long
    as it takes to fill the input buffer.

    Args:
     Latency (float): Maximum output latency (seconds)

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._max_latency = Latency
    return self

  def _flush_buffer(self, EventTypeName, EventSourceId, EventGroupId, Merge):

    if not self._writing_events:
      self._write_ontology()
      self._writer.OpenEventGroups()
      self._writing_events = True

    if self._current_event_group_type != EventTypeName or self._current_event_group_source != EventSourceId:
      if self._current_event_group_type is not None:
        self._writer.CloseEventGroup()
      self._writer.OpenEventGroup(EventTypeName, EventSourceId)
      self._current_event_group_type = EventTypeName
      self._current_event_group_source = EventSourceId

    Events = self._event_buffers[EventGroupId][Merge].itervalues() if Merge else self._event_buffers[EventGroupId][Merge]

    for Event in Events:
      try:
        self._writer.AddEvent(Event[0], Event[1], Event[2], IgnoreInvalidObjects=self._ignore_invalid_objects)
      except EDXMLError as Error:
        if self._ignore_invalid_events:
          if self._log_invalid_events:
            self._writer.Warning(str(Error) + '\n\nContinuing anyways.\n')
        else:
          raise

    self._last_write_time = time.time()
    self._event_buffers[EventGroupId][Merge] = {} if Merge else []

  def Close(self):
    """

    Finalizes the output stream generation process. This method
    must be called to yield a complete, valid output stream.

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """

    for GroupId in self._event_buffers:
      EventTypeName, EventSourceId = GroupId.split(':')
      for Merge in self._event_buffers[GroupId]:
        if len(self._event_buffers[GroupId][Merge]) > 0:
          self._flush_buffer(EventTypeName, EventSourceId, GroupId, Merge)

    if self._current_event_group_type is not None:
      self._writer.CloseEventGroup()
      self._writer.CloseEventGroups()
      self._current_event_group_type = None

    return self
