# -*- coding: utf-8 -*-
from edxml.EDXMLBase import EDXMLError
import edxml.transcode.mediator


class JsonTranscoderMediator(edxml.transcode.mediator.TranscoderMediator):
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
  transcoder. If there is no fallback transcoder available, the record will not
  be processed.

  Note:
    The fallback transcoder is a transcoder that registered itself as a transcoder
    for the record type named 'RECORD_OF_UNKNOWN_TYPE', which is a reserved name.
  """

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
      record type named 'RECORD_OF_UNKNOWN_TYPE' is used as the fallback
      transcoder. The fallback transcoder is used to transcode any record
      that has a record type for which no transcoder has been registered.

    Args:
      RecordTypeName (str): Name of the JSON record type
      Transcoder (JsonTranscoder): JsonTranscoder class
    """
    edxml.transcode.mediator.TranscoderMediator.Register(RecordTypeName, Transcoder)

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
    return edxml.transcode.mediator.TranscoderMediator.GetTranscoder(RecordTypeName)

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
      RecordType = JsonData.get(self.TYPE_FIELD, 'RECORD_OF_UNKNOWN_TYPE')
    else:
      RecordType = getattr(JsonData, self.TYPE_FIELD, 'RECORD_OF_UNKNOWN_TYPE')
    Transcoder  = self.GetTranscoder(RecordType)

    if not Transcoder and RecordType != 'RECORD_OF_UNKNOWN_TYPE':
      # No transcoder available for record type,
      # use the fallback transcoder, if available.
      Transcoder = self.GetTranscoder('RECORD_OF_UNKNOWN_TYPE')

    if Transcoder:

      if RecordType == 'RECORD_OF_UNKNOWN_TYPE' and self.TYPE_FIELD and self._warn_fallback:
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

        if self._transcoderIsPostprocessor(Transcoder):
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
            if not self._ignore_invalid_events or self._debug:
              raise
            if self._warn_invalid_events:
              self.Warning(('The post processor of the transcoder for JSON record type %s failed '
                            'with %s: %s\n\nContinuing...') % (RecordType, type(Except).__name__, str(Except))
                           )
        else:
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
      if self._warn_no_transcoder:
        if RecordType == 'RECORD_OF_UNKNOWN_TYPE' and self.TYPE_FIELD:
          self.Warning('JSON record has no "%s" field and no fallback transcoder available.' % self.TYPE_FIELD)
        else:
          self.Warning(('No transcoder registered itself as fallback (record type "RECORD_OF_UNKNOWN_TYPE"), '
                        'no %s event generated.') % RecordType
                       )
        self.Warning('Record was: %s' % JsonData)
