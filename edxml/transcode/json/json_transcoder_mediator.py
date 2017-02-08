# -*- coding: utf-8 -*-
from edxml import Ontology
from edxml.EDXMLBase import EDXMLBase, EDXMLError
from edxml.SimpleEDXMLWriter import SimpleEDXMLWriter
from edxml.ontology import EventSource

class JsonTranscoderMediator(EDXMLBase):
  """
  This class is a mediator between a source of JSON records and a set
  of JsonTranscoder implementations that can transcode the JSON records
  into EDXML events.

  Sources can instantiate the mediator and feed it JSON records, while
  transcoders can register themselves with the mediator in order to
  transcode the types of JSON record that they support.
  """

  TYPE_FIELD = None
  """
  This constant must be set to the name of the field in the root of the JSON record
  that contains the JSON record type, allowing the Transcoder Manager to route
  JSON records to the correct transcoder.

  If the constant is set to None, all JSON records will be routed to the fallback
  transcoder. If there is not fallback transcoder available, the record will not
  be processed.

  Note:
    The fallback transcoder is a transcoder that registered itself as a transcoder
    for the record type named 'JSON_OF_UNKNOWN_TYPE', which is a reserved name.
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

    super(JsonTranscoderMediator, self).__init__()
    self._output = Output
    self._writer = None   # var: edxml.SimpleEDXMLWriter
    self._ontology = Ontology()
    self._last_written_ontology_version = self._ontology.GetVersion()

  @classmethod
  def Register(cls, RecordTypeName, Transcoder):
    """

    Register a transcoder for processing records of specified
    type. The same transcoder can be registered for multiple
    record types. The Transcoder argument must be a JsonTranscoder
    class or an extension of it. Do not pass in instantiated
    class, pass the class itself.

    Note:
      Any transcoder that registers itself as a transcoder for the
      record type named 'JSON_OF_UNKNOWN_TYPE' is used as the fallback
      transcoder. The fallback transcoder is used to transcode any record
      that has a record type for which no transcoder has been registered.

    Args:
      RecordTypeName (str): Name of the JSON record type
      Transcoder (JsonTranscoder): JsonTranscoder class
    """
    cls._transcoders[RecordTypeName] = Transcoder()
    cls._auto_merge_eventtypes.extend(cls._transcoders[RecordTypeName].GetAutoMergeEventTypes())

  def Debug(self):
    """
    Enable debugging mode, which prints informative
    messages about JSON transcoding issues, disables
    event buffering and stops on errors.

    Returns:
      JsonTranscoderMediator:
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
      JsonTranscoderMediator:
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
      JsonTranscoderMediator:
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
      JsonTranscoderMediator:
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
  def GetTranscoder(cls, RecordTypeName):
    """

    Returns a JsonTranscoder instance for transcoding
    records of specified type, or None if no transcoder
    has been registered for the record type.

    Args:
      RecordTypeName (str): Name of the JSON record type

    Returns:
      JsonTranscoder:
    """

    if RecordTypeName in cls._transcoders:
      return cls._transcoders[RecordTypeName]
    else:
      return cls._transcoders.get('JSON_OF_UNKNOWN_TYPE', None)

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

  def Process(self, JsonData):
    """
    Processes a single JSON record, invoking the correct
    transcoder to generate an EDXML event and writing the
    event into the output.

    The JSON record must be represented as either a dictionary
    or an object. When an object is passed, it will attempt to
    read any attributes listed in the ATTRIBUTE_MAP of the matching
    transcoder from object attributes. When a dictionary is passed,
    it will attempt to read keys as listed in ATTRIBUTE_MAP. Using
    dotted notation, the keys in ATTRIBUTE_MAP can refer to dictionary
    values that are themselves dictionaries of lists.

    Args:
      JsonData (dict,object): Json dictionary
    """
    if type(JsonData) == dict:
      RecordType = JsonData.get(self.TYPE_FIELD, 'JSON_OF_UNKNOWN_TYPE')
    else:
      RecordType = getattr(JsonData, self.TYPE_FIELD, 'JSON_OF_UNKNOWN_TYPE')
    Transcoder  = self.GetTranscoder(RecordType)

    if not Transcoder and RecordType != 'JSON_OF_UNKNOWN_TYPE':
      # No transcoder available for record type,
      # use the fallback transcoder, if available.
      Transcoder = self.GetTranscoder('JSON_OF_UNKNOWN_TYPE')

    if Transcoder:

      if RecordType == 'JSON_OF_UNKNOWN_TYPE' and self.TYPE_FIELD and self._debug:
        self.Warning('JSON record has no "%s" field, passing to fallback transcoder' % self.TYPE_FIELD)
        self.Warning('Record was: %s' % JsonData)

      for Event in Transcoder.Generate(JsonData, RecordType):
        if not self._writer:
          # Apparently, this is the first event that
          # is generated. Create an EDXML writer and
          # write the initial ontology.
          self._create_writer()
          self._write_initial_ontology()
        if self._ontology.IsModifiedSince(self._last_written_ontology_version):
          # Ontology was changed since we wrote the last ontology update,
          # so we need to write another update.
          self._write_ontology_update()
          self._last_written_ontology_version = self._ontology.GetVersion()

        if Transcoder.IsPostProcessor():
          try:
            for PostProcessedEvent in Transcoder.PostProcess(Event):
              try:
                self._writer.AddEvent(PostProcessedEvent)
              except StopIteration:
                self._writer.Close()
                pass
              except EDXMLError as Except:
                if not self._ignore_invalid_events:
                  raise
                if self._warn_invalid_events:
                  self.Warning(('The post processor of the transcoder for JSON record type %s produced '
                                'an invalid event: %s\n\nContinuing...') % (RecordType, str(Except))
                               )
          except Exception as Except:
            if self._debug:
              raise
            self.Warning(('The post processor of the transcoder for JSON record type %s failed '
                          'with %s: %s\n\nContinuing...') % (RecordType, type(Except).__name__, str(Except))
                         )

        try:
          self._writer.AddEvent(Event)
        except StopIteration:
          self._writer.Close()
          pass
        except EDXMLError as Except:
          if not self._ignore_invalid_events:
            raise
          if self._warn_invalid_events:
            self.Warning(('The transcoder for JSON record type %s produced an invalid '
                          'event: %s\n\nContinuing...') % (RecordType, str(Except)))
        except Exception as Except:
          if self._debug:
            raise
          self.Warning(('Transcoder for JSON record type %s failed '
                        'with %s: %s\n\nContinuing...') % (RecordType, type(Except).__name__, str(Except))
                       )
    else:
      if self._debug:
        if RecordType == 'JSON_OF_UNKNOWN_TYPE' and self.TYPE_FIELD:
          self.Warning('JSON record has no "%s" field and no fallback transcoder available.' % self.TYPE_FIELD)
        else:
          self.Warning(('No transcoder registered itself as fallback (record type "JSON_OF_UNKNOWN_TYPE"), '
                        'no %s event generated.') % RecordType
                       )
        self.Warning('Record was: %s' % JsonData)

  def Close(self):
    """
    Finalizes the transcoding process by flushing
    the output buffer.
    """
    if self._writer:
      self._writer.Close()
