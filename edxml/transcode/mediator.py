# -*- coding: utf-8 -*-
from edxml.transcode.transcoder import Transcoder

from edxml import Ontology
from edxml.EDXMLBase import EDXMLBase
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
  """

  _transcoders = {}
  _sources = []

  _debug = False
  _validate_events = True
  _ignore_invalid_objects = False
  _ignore_invalid_events = False
  _auto_merge_eventtypes = []
  _warn_invalid_events = False

  def __init__(self, Output):

    super(TranscoderMediator, self).__init__()
    self._output = Output
    self._writer = None   # var: edxml.SimpleEDXMLWriter
    self._ontology = Ontology()
    self._last_written_ontology_version = self._ontology.GetVersion()

  @staticmethod
  def _transcoderIsPostprocessor(transcoder):
    thisMethod = getattr(transcoder, 'PostProcess')
    baseMethod = getattr(Transcoder, 'PostProcess')
    return thisMethod.__func__ is not baseMethod.__func__

  @classmethod
  def Register(cls, RecordIdentifier, Transcoder):
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
      Transcoder (Transcoder): Transcoder class
    """
    cls._transcoders[RecordIdentifier] = Transcoder()
    cls._auto_merge_eventtypes.extend(cls._transcoders[RecordIdentifier].GetAutoMergeEventTypes())

  def Debug(self):
    """
    Enable debugging mode, which prints informative
    messages about transcoding issues, disables
    event buffering and stops on errors.

    Returns:
      TranscoderMediator:
    """
    self._debug = True

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

    if RecordSelector in cls._transcoders:
      return cls._transcoders[RecordSelector]
    else:
      return cls._transcoders.get('RECORD_OF_UNKNOWN_TYPE', None)

  def _write_initial_ontology(self):
    # Here, we write the ontology elements that are
    # defined by the various transcoders.
    for Transcoder in self._transcoders.values():
      Transcoder.SetOntology(self._ontology)

    for Transcoder in self._transcoders.values():
      for _ in Transcoder.GenerateObjectTypes():
        # Here, we only populate the ontology, we
        # don't do anything with the ontology elements.
        pass

    for Transcoder in self._transcoders.values():
      for _ in Transcoder.GenerateConcepts():
        # Here, we only populate the ontology, we
        # don't do anything with the ontology elements.
        pass

    for Transcoder in self._transcoders.values():
      for _, _ in Transcoder.GenerateEventTypes():
        # Here, we only populate the ontology, we
        # don't do anything with the ontology elements.
        pass

    if len(self._sources) == 0:
      self.Warning('No EDXML source was defined, generating bogus source.')
      self._sources.append(self._ontology.CreateEventSource('/undefined/'))

    # Add the generated ontology elements and
    # create a new, empty ontology for accumulating
    # ontology updates that may generated later, by event
    # transcoders.
    self._writer.AddOntology(self._ontology)
    self._last_written_ontology_version = self._ontology.GetVersion()

  def _write_ontology_update(self):
    # Here, we write ontology updates resulting
    # from adding new ontology elements while
    # generating events. Currently, this is limited
    # to event source definitions.
    self._writer.AddOntology(self._ontology)

  def _create_writer(self):
    self._writer = SimpleEDXMLWriter(self._output, self._validate_events)
    if self._debug:
      self._writer.SetBufferSize(1)
    if self._ignore_invalid_objects:
      self._writer.IgnoreInvalidObjects()
    if self._ignore_invalid_events:
      self._writer.IgnoreInvalidEvents(self._warn_invalid_events)
    for EventTypeName in self._auto_merge_eventtypes:
      self._writer.AutoMerge(EventTypeName)

  def Process(self, DataRecord):
    """
    Processes a single input record, invoking the correct
    transcoder to generate an EDXML event and writing the
    event into the output.

    Args:
      DataRecord: Input data record
    """
    return

  def Close(self):
    """
    Finalizes the transcoding process by flushing
    the output buffer.
    """
    if self._writer:
      self._writer.Close()
