# -*- coding: utf-8 -*-
from typing import Dict

import edxml

from edxml.transcode import Transcoder
from edxml.ontology import Ontology
from edxml.EDXMLBase import EDXMLBase, EDXMLValidationError
from edxml.SimpleEDXMLWriter import SimpleEDXMLWriter
from edxml.ontology import EventSource


class TranscoderMediator(EDXMLBase):
  """
  Base class for implementing mediators between a non-EDXML input data source
  and a set of Transcoder implementations that can transcode the input data records
  into EDXML events.

  Sources can instantiate the mediator and feed it input data records, while
  transcoders can register themselves with the mediator in order to
  transcode the types of input record that they support.

  The class is a Python context manager which will automatically flush the
  output buffer when the mediator goes out of scope.
  """

  _record_transcoders = {}
  _transcoders = {}  # type: Dict[any, edxml.transcode.Transcoder]
  _sources = []

  _debug = False
  _disable_buffering = False
  _warn_no_transcoder = False
  _warn_fallback = False

  _validate_events = True
  _ignore_invalid_objects = False
  _ignore_invalid_events = False
  _log_repaired_events = False
  _auto_merge_eventtypes = []
  _warn_invalid_events = False
  _defaultSourceUri = None

  def __init__(self, Output=None):
    """

    Create a new transcoder mediator which will output streaming
    EDXML data using specified output. The Output parameter is a
    file-like object that will be used to send the XML data to.
    This file-like object can be pretty much anything, as long
    as it has a write() method and a mode containing 'a' (opened
    for appending). When the Output parameter is omitted, the
    generated XML data will be returned or yielded by the methods
    that generate output.

    Args:
      Output (file, optional): a file-like object
    """

    super(TranscoderMediator, self).__init__()
    self._output = Output
    self._writer = None   # var: edxml.SimpleEDXMLWriter
    self._ontology = Ontology()
    self._last_written_ontology_version = self._ontology.GetVersion()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    # If mediator exits due to an EDXML validation exception
    # triggered by the EDXML writer, we will not flush the event
    # output buffer. We do that to prevent us from outputting
    # invalid EDXML data. For other kinds of exceptions, like
    # KeyboardInterrupt, flushing the# output buffers is fine.
    self.Close(flush=exc_type != EDXMLValidationError)

  @staticmethod
  def _transcoderIsPostprocessor(transcoder):
    thisMethod = getattr(transcoder, 'PostProcess')
    baseMethod = getattr(Transcoder, 'PostProcess')
    return thisMethod.__func__ is not baseMethod.__func__

  @classmethod
  def Register(cls, RecordIdentifier, RecordTranscoder):
    """

    Register a transcoder for processing records identified by
    the specified record selector. The exact nature of the record
    selector depends on the mediator implementation.

    The same transcoder can be registered for multiple
    record selectors. The Transcoder argument must be a Transcoder
    class or an extension of it. Do not pass in instantiated
    class, pass the class itself.

    Note:
      Any transcoder that registers itself as a transcoder for the
      record selector string 'RECORD_OF_UNKNOWN_TYPE' is used as the fallback
      transcoder. The fallback transcoder is used to transcode any record
      for which no transcoder has been registered.

    Args:
      RecordIdentifier: Record type identifier
      RecordTranscoder (class): Transcoder class
    """
    if RecordTranscoder not in cls._transcoders:
      cls._transcoders[RecordTranscoder] = RecordTranscoder()
      cls._auto_merge_eventtypes.extend(cls._transcoders[RecordTranscoder].GetAutoMergeEventTypes())

    cls._record_transcoders[RecordIdentifier] = RecordTranscoder

  def Debug(self, disableBuffering=True, warnNoTranscoder=True, warnFallback=True, logRepairedEvents=True):
    """
    Enable debugging mode, which prints informative
    messages about transcoding issues, disables
    event buffering and stops on errors.

    Using the keyword arguments, specific debug features
    can be disabled. When warnNoTranscoder is set to False,
    no warnings will be generated when no matching transcoder
    can be found. When warnFallback is set to False, no
    warnings will be generated when an input record is routed
    to the fallback transcoder. When logRepairedEvents is set
    to False, no message will be generated when an invalid
    event was repaired.

    Args:
      disableBuffering  (bool): Disable output buffering
      warnNoTranscoder  (bool): Warn when no transcoder found
      warnFallback      (bool): Warn when using fallback transcoder
      logRepairedEvents (bool): Log events that were repaired

    Returns:
      TranscoderMediator:
    """
    self._debug = True
    self._disable_buffering = disableBuffering
    self._warn_no_transcoder = warnNoTranscoder
    self._warn_fallback = warnFallback
    self._log_repaired_events = logRepairedEvents

    return self

  def DisableEventValidation(self):
    """
    Instructs the EDXML writer not to validate its
    output. This may be used to boost performance in
    case you know that the data will be validated at
    the receiving end, or in case you know that your
    generator is perfect. :)

    Returns:
     TranscoderMediator:
    """
    self._validate_events = False
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
      TranscoderMediator:
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
      Warn (bool): Print warnings or not

    Returns:
      TranscoderMediator:
    """
    self._ignore_invalid_events = True
    self._warn_invalid_events = Warn
    return self

  def AddEventSource(self, SourceUri):
    """

    Adds an EDXML event source definition. If no event sources
    are added, a bogus source will be generated.

    Warning:
      The source URI is used to compute sticky
      hashes. Therefore, adjusting the source URIs of events
      after generating them changes their hashes.

    The mediator will not output the EDXML ontology until
    it receives its first event through the Process() method.
    This means that the caller can generate an event source
    'just in time' by inspecting the input record and use this
    method to create the appropriate source definition.

    Returns the created EventSource instance, to allow it to
    be customized.

    Args:
      SourceUri (str): An Event Source URI

    Returns:
      EventSource:
    """
    source = self._ontology.CreateEventSource(SourceUri)
    self._sources.append(source)
    return source

  def SetEventSource(self, SourceUri):
    """

    Set the default event source for the output events. If no explicit
    source is set on an output event, the default source will
    be used.

    Args:
      SourceUri (str): The event source URI

    Returns:
      TranscoderMediator:
    """
    self._defaultSourceUri = SourceUri
    if self._writer:
      self._writer.SetEventSource(SourceUri)

    return self

  @classmethod
  def GetTranscoder(cls, RecordSelector):
    """

    Returns a Transcoder instance for transcoding
    records matching specified selector, or None if no transcoder
    has been registered for records of that selector.

    Args:
      RecordSelector (str): record type selector

    Returns:
      Transcoder:
    """

    if RecordSelector in cls._record_transcoders:
      return cls._transcoders[cls._record_transcoders[RecordSelector]]
    else:
      return cls._transcoders.get(cls._record_transcoders.get('RECORD_OF_UNKNOWN_TYPE'))

  def _write_initial_ontology(self):
    # Here, we write the ontology elements that are
    # defined by the various transcoders.

    # First, we accumulate the object types into an
    # empty ontology.
    objectTypes = Ontology()
    for transcoder in self._transcoders.values():
      transcoder.SetOntology(objectTypes)
      for _ in transcoder.GenerateObjectTypes():
        # Here, we only populate the list of object types,
        # we don't do anything with them.
        pass

    # Add the object types to the main mediator ontology
    self._ontology.Update(objectTypes)

    # Then, we accumulate the concepts into an
    # empty ontology.
    concepts = Ontology()
    for transcoder in self._transcoders.values():
      transcoder.SetOntology(concepts)
      for _ in transcoder.GenerateConcepts():
        # Here, we only populate the list of concepts,
        # we don't do anything with them.
        pass

    # Add the concepts to the main mediator ontology
    self._ontology.Update(concepts)

    # Now, we allow each of the transcoders to create their event
    # types in separate ontologies. We do that to allow two transcoders
    # to create two event types that share the same name. That is
    # a common pattern in transcoders that inherit event type definitions
    # from their parent, adjust the event type and finally rename it.
    for transcoder in self._transcoders.values():
      transcoder.SetOntology(Ontology())
      transcoder.UpdateOntology(objectTypes, validate=False)
      transcoder.UpdateOntology(concepts, validate=False)
      for _, _ in transcoder.GenerateEventTypes():
        # Here, we only populate the ontology, we
        # don't do anything with the ontology elements.
        self._ontology.Update(transcoder._ontology, validate=False)
        transcoder.UpdateOntology(objectTypes, validate=False)
        transcoder.UpdateOntology(concepts, validate=False)
        transcoder.SetOntology(Ontology())

    if len(self._sources) == 0:
      self.Warning('No EDXML source was defined, generating bogus source.')
      self._sources.append(self._ontology.CreateEventSource('/undefined/'))

    self._writer.AddOntology(self._ontology)
    self._last_written_ontology_version = self._ontology.GetVersion()

  def _write_ontology_update(self):
    # Here, we write ontology updates resulting
    # from adding new ontology elements while
    # generating events. Currently, this is limited
    # to event source definitions.
    return self._writer.AddOntology(self._ontology)

  def _create_writer(self):
    self._writer = SimpleEDXMLWriter(self._output, self._validate_events)
    if self._defaultSourceUri:
      self._writer.SetEventSource(self._defaultSourceUri)
    if self._disable_buffering:
      self._writer.SetBufferSize(0)
    if self._ignore_invalid_objects:
      self._writer.IgnoreInvalidObjects()
    if self._ignore_invalid_events:
      self._writer.IgnoreInvalidEvents(self._warn_invalid_events)
    if self._log_repaired_events:
      self._writer.LogRepairedEvents()
    for EventTypeName in self._auto_merge_eventtypes:
      self._writer.AutoMerge(EventTypeName)

  def Process(self, DataRecord):
    """
    Processes a single input record, invoking the correct
    transcoder to generate an EDXML event and writing the
    event into the output.

    If no output was specified while instantiating this class,
    any generated XML data will be returned as unicode string.

    Args:
      DataRecord: Input data record

    Returns:
      unicode: Generated output XML data

    """
    return u''

  def Close(self, flush=True):
    """
    Finalizes the transcoding process by flushing
    the output buffer. When the mediator is not used
    as a context manager, this method must be called
    explicitly to properly close the mediator.

    By default, any remaining events in the output buffer will
    be written to the output, unless flush is set to False.

    If no output was specified while instantiating this class,
    any generated XML data will be returned as unicode string.

    Args:
      flush (bool): Flush output buffer

    Returns:
      unicode: Generated output XML data

    """
    if self._writer:
      return self._writer.Close(flush)
    else:
      return u''
