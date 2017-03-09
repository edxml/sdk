# -*- coding: utf-8 -*-
import time

from edxml.EDXMLWriter import EDXMLWriter
from edxml.EDXMLBase import EDXMLError, EDXMLValidationError
from edxml.EDXMLEvent import EDXMLEvent
from edxml.ontology import Ontology


class SimpleEDXMLWriter(object):
  """High level EDXML stream writer

  This class offers a simplified interface to
  the EDXMLWriter class. Apart from a simplified
  interface, it implements some additional features
  like buffering, post-processing, automatic merging
  of output events and latency control.

  """

  def __init__(self, Output, Validate=True):
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

    Returns:
       SimpleEDXMLWriter:
    """

    self.__maxBufSize = 1024
    self.__currBufSize = 0
    self._output = Output
    self._validate = Validate
    self._max_latency = 0
    self._last_write_time = time.time()
    self._ignore_invalid_objects = False
    self._ignore_invalid_events = False
    self._log_invalid_events = False
    self._currentSourceUri = None
    self._current_event_type = None
    self._current_event_group_source = None
    self._current_event_group_type = None
    self._event_buffers = {}
    self._ontology = Ontology()
    self._last_written_ontology_version = self._ontology.GetVersion()
    self._event_type_postprocessors = {}
    self._automerge = {}
    self._writer = None

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    # If writer exits due to an EDXML validation exception,
    # we will not flush the event output buffer. We do that to
    # prevent us from outputting invalid EDXML data. For other
    # kinds of exceptions, like KeyboardInterrupt, flushing the
    # output buffers is fine.
    self.Close(flush=exc_type != EDXMLValidationError)

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

  def AddOntology(self, edxmlOntology):
    """

    Add all definitions in specified ontology to the ontology that
    is written into the output EDXML stream.

    Args:
      edxmlOntology (edxml.ontology.Ontology): The EDXML ontology

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance

    """
    self._ontology.Update(edxmlOntology)
    return self

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

  def SetEventSource(self, SourceUri):
    """

    Set the default event source for the output events. If no explicit
    source is specified in calls to AddEvent(), the default source will
    be used.

    Args:
      SourceUri (str): The event source URI

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """
    self._currentSourceUri = SourceUri

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
      Event.SourceUri
    )

  def GenerateEvent(self, Properties, Content=u'', Parents=None, Type=None, Source=None):
    """

    Generate a new event and write to the output stream. If the event type or
    event source are not specified, the default type and source that
    have been set using SetEventType() and SetEventSource() will be used.

    The Properties dictionary must have keys containing the property names. The values
    of the dictionary must be object values or lists of object values. Object values
    can be anything can be cast to a unicode object.

    Args:
      Properties (dict[str]): The event properties
      Content (unicode): Event content string
      Parents (list[str], Optional): List of sticky hashes, as hex strings
      Type (str, Optional): Event type name
      Source (str, Optional): EDXML event source URI

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """

    EventSourceUri = Source or self._currentSourceUri
    EventTypeName = Type or self._current_event_type
    if EventSourceUri is None:
      if len(self._ontology.GetEventSources()) == 1:
        EventSourceUri = self._ontology.GetEventSources().keys()[0]
      else:
        raise EDXMLError('No event source was specified.')

    if EventTypeName is None:
      if len(self._ontology.GetEventTypeNames()) == 1:
        EventTypeName = self._ontology.GetEventTypeNames()[0]
      else:
        raise EDXMLError('No event type was specified.')

    if EventTypeName in self._event_type_postprocessors:
      self._event_type_postprocessors[EventTypeName](Properties, Content, Parents, EventTypeName, EventSourceUri)

    Event = EDXMLEvent.Create(Properties, EventTypeName, EventSourceUri, Parents, Content)

    EventGroup = '%s:%s' % (EventTypeName, EventSourceUri)
    if not EventGroup in self._event_buffers:
      self._event_buffers[EventGroup] = {True: {}, False: []}

    Merge = EventTypeName in self._automerge
    if Merge:
      # We need to compute the sticky hash, check
      # for collisions and merge if needed.
      Hash = Event.Normalize(self._ontology).ComputeStickyHash(self._ontology)

      if Hash not in self._event_buffers[EventGroup][Merge]:
        self._event_buffers[EventGroup][Merge][Hash] = [Event]
      else:
        self._event_buffers[EventGroup][Merge][Hash].append(Event)
    else:
      self._event_buffers[EventGroup][Merge].append(Event)

    self.__currBufSize += 1

    if self.__currBufSize > self.__maxBufSize or \
       0 < self._max_latency <= (time.time() - self._last_write_time):
       self._flush_buffer(EventTypeName, EventSourceUri, EventGroup, Merge)

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
    self.__maxBufSize = EventCount
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

  def _flush_buffer(self, EventTypeName, EventSourceUri, EventGroupId, Merge):

    if not self._writer:
      # We did not create the EDXMLWriter yet.
      self._writer = EDXMLWriter(self._output, self._validate)
      self._writer.AddOntology(self._ontology)
      self._last_written_ontology_version = self._ontology.GetVersion()
      self._writer.OpenEventGroups()

    if self._ontology.IsModifiedSince(self._last_written_ontology_version):
      # TODO: Rather than outputting a complete, new
      # ontology, we should only output the ontology
      # elements that are new or updated.
      if self._current_event_group_type is not None:
        self._writer.CloseEventGroup()
        self._current_event_group_type = None
      self._writer.CloseEventGroups()
      self._writer.AddOntology(self._ontology)
      self._last_written_ontology_version = self._ontology.GetVersion()
      self._writer.OpenEventGroups()
    if self._current_event_group_type != EventTypeName or self._current_event_group_source != EventSourceUri:
      if self._current_event_group_type is not None:
        self._writer.CloseEventGroup()
      self._writer.OpenEventGroup(EventTypeName, EventSourceUri)
      self._current_event_group_type = EventTypeName
      self._current_event_group_source = EventSourceUri

    if Merge:
      for Hash, Events in self._event_buffers[EventGroupId][Merge].items():
        if (len(Events)) > 1:
          FirstEvent = self._event_buffers[EventGroupId][Merge][Hash].pop()
          self._event_buffers[EventGroupId][Merge][Hash] = FirstEvent.MergeWith(Events, self._ontology)
        else:
          self._event_buffers[EventGroupId][Merge][Hash] = self._event_buffers[EventGroupId][Merge][Hash].pop()

    Events = self._event_buffers[EventGroupId][Merge].itervalues() if Merge else self._event_buffers[EventGroupId][Merge]

    for Event in Events:
      try:
        self._writer.AddEvent(Event)
      except EDXMLValidationError as Error:
        if self._ignore_invalid_events:
          if self._log_invalid_events:
            self._writer.Warning(str(Error) + '\n\nContinuing anyways.\n')
        else:
          raise

    self._last_write_time = time.time()
    self.__currBufSize = 0
    self._event_buffers[EventGroupId][Merge] = {} if Merge else []

  def Close(self, flush=True):
    """

    Finalizes the output stream generation process. This method
    must be called to yield a complete, valid output stream.

    By default, any remaining events in the output buffer will
    be written, unless flush is set to False.

    Args:
      flush (bool): Flush output buffer

    Returns:
      SimpleEDXMLWriter: The SimpleEDXMLWriter instance
    """

    if not self._writer:
      # We did not create the EDXMLWriter yet.
      self._writer = EDXMLWriter(self._output, self._validate)

    if flush and self._ontology.IsModifiedSince(self._last_written_ontology_version):
      if self._current_event_group_type is not None:
        self._writer.CloseEventGroup()
        self._writer.CloseEventGroups()
        self._current_event_group_type = None
      self._writer.AddOntology(self._ontology)
      self._last_written_ontology_version = self._ontology.GetVersion()

    for GroupId in self._event_buffers:
      EventTypeName, EventSourceUri = GroupId.split(':')
      for Merge in self._event_buffers[GroupId]:
        if flush and len(self._event_buffers[GroupId][Merge]) > 0:
          self._flush_buffer(EventTypeName, EventSourceUri, GroupId, Merge)

    if self._current_event_group_type is not None:
      self._writer.CloseEventGroup()
      self._current_event_group_type = None

    self._writer.Close()
    return self
