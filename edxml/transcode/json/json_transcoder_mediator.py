# -*- coding: utf-8 -*-

import edxml.transcode.mediator

from edxml.EDXMLBase import EDXMLError


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
    def register(cls, record_type_identifier, transcoder):
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
          record_type_identifier (str): Name of the JSON record type
          transcoder (JsonTranscoder): JsonTranscoder class
        """
        edxml.transcode.mediator.TranscoderMediator.register(
            record_type_identifier, transcoder)

    @classmethod
    def _get_transcoder(cls, record_type_name):
        """

        Returns a JsonTranscoder instance for transcoding
        records of specified type, or None if no transcoder
        has been registered for the record type.

        Args:
          record_type_name (str): Name of the JSON record type

        Returns:
          JsonTranscoder:
        """
        return edxml.transcode.mediator.TranscoderMediator._get_transcoder(record_type_name)

    def process(self, json_record):
        """
        Processes a single JSON record, invoking the correct
        transcoder to generate an EDXML event and writing the
        event into the output.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as unicode string.

        The JSON record must be represented as either a dictionary
        or an object. When an object is passed, it will attempt to
        read any attributes listed in the PROPERTY_MAP of the matching
        transcoder from object attributes. When a dictionary is passed,
        it will attempt to read keys as listed in PROPERTY_MAP. Using
        dotted notation, the keys in PROPERTY_MAP can refer to dictionary
        values that are themselves dictionaries of lists.

        Args:
          json_record (dict,object): Json dictionary

        Returns:
          unicode: Generated output XML data

        """

        outputs = []

        if self.TYPE_FIELD is None:
            # Type field is not set, which means we must use the
            # fallback transcoder.
            record_type = 'RECORD_OF_UNKNOWN_TYPE'
        else:
            try:
                record_type = json_record.get(
                    self.TYPE_FIELD, 'RECORD_OF_UNKNOWN_TYPE')
            except AttributeError:
                record_type = getattr(
                    json_record, self.TYPE_FIELD, 'RECORD_OF_UNKNOWN_TYPE')

        transcoder = self._get_transcoder(record_type)

        if not transcoder and record_type != 'RECORD_OF_UNKNOWN_TYPE':
            # No transcoder available for record type,
            # use the fallback transcoder, if available.
            transcoder = self._get_transcoder('RECORD_OF_UNKNOWN_TYPE')

        if transcoder:

            if record_type == 'RECORD_OF_UNKNOWN_TYPE' and self.TYPE_FIELD and self._warn_fallback:
                self.warning(
                    'JSON record has no "%s" field, passing to fallback transcoder' % self.TYPE_FIELD)
                self.warning('Record was: %s' % json_record)

            for Event in transcoder.generate(json_record, record_type):
                if self._output_source_uri:
                    Event.set_source_uri(self._output_source_uri)
                if not self._writer:
                    # Apparently, this is the first event that
                    # is generated. Create an EDXML writer and
                    # write the initial ontology.
                    self._create_writer()
                    self._write_initial_ontology()
                if self._ontology.is_modified_since(self._last_written_ontology_version):
                    # Ontology was changed since we wrote the last ontology update,
                    # so we need to write another update.
                    self._write_ontology_update()
                    self._last_written_ontology_version = self._ontology.get_version()

                if self._transcoder_is_postprocessor(transcoder):
                    try:
                        for PostProcessedEvent in transcoder.post_process(Event, json_record):
                            try:
                                outputs.append(
                                    self._writer.add_event(PostProcessedEvent))
                            except StopIteration:
                                outputs.append(self._writer.close())
                            except EDXMLError as Except:
                                if not self._ignore_invalid_events:
                                    raise
                                if self._warn_invalid_events:
                                    self.warning(
                                        ('The post processor of the transcoder for JSON record type %s produced '
                                         'an invalid event: %s\n\nContinuing...') % (record_type, str(Except))
                                    )
                    except Exception as Except:
                        if not self._ignore_invalid_events or self._debug:
                            raise
                        if self._warn_invalid_events:
                            self.warning(
                                ('The post processor of the transcoder for JSON record type %s failed '
                                 'with %s: %s\n\nContinuing...') % (record_type, type(Except).__name__, str(Except))
                            )
                else:
                    try:
                        outputs.append(self._writer.add_event(Event))
                    except StopIteration:
                        outputs.append(self._writer.close())
                    except EDXMLError as Except:
                        if not self._ignore_invalid_events:
                            raise
                        if self._warn_invalid_events:
                            self.warning(('The transcoder for JSON record type %s produced an invalid '
                                          'event: %s\n\nContinuing...') % (record_type, str(Except)))
                    except Exception as Except:
                        if self._debug:
                            raise
                        self.warning(
                            'Transcoder for JSON record type %s failed '
                            'with %s: %s\n\nContinuing...' % (record_type, type(Except).__name__, str(Except))
                        )
        else:
            if self._warn_no_transcoder:
                if record_type == 'RECORD_OF_UNKNOWN_TYPE' and self.TYPE_FIELD:
                    self.warning(
                        'JSON record has no "%s" field and no fallback transcoder available.' % self.TYPE_FIELD)
                else:
                    self.warning(('No transcoder registered itself as fallback (record type "RECORD_OF_UNKNOWN_TYPE"), '
                                  'no %s event generated.') % record_type
                                 )
                self.warning('Record was: %s' % json_record)

        return u''.join(outputs)
