# -*- coding: utf-8 -*-
from typing import Dict

import edxml
from edxml.transcode import Transcoder
from edxml.ontology import Ontology
from edxml.EDXMLBase import EDXMLBase, EDXMLValidationError
from edxml.SimpleEDXMLWriter import SimpleEDXMLWriter


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

    __record_transcoders = {}
    __transcoders = {}  # type: Dict[any, edxml.transcode.Transcoder]
    __sources = []

    _debug = False
    _warn_no_transcoder = False
    _warn_fallback = False
    _warn_invalid_events = False
    _ignore_invalid_objects = False
    _ignore_invalid_events = False
    _output_source_uri = None

    __disable_buffering = False
    __validate_events = True
    __log_repaired_events = False
    __auto_merge_eventtypes = []

    def __init__(self, output=None):
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
          output (file, optional): a file-like object
        """

        super(TranscoderMediator, self).__init__()
        self.__output = output
        self._writer = None   # var: edxml.SimpleEDXMLWriter
        self._ontology = Ontology()
        self._last_written_ontology_version = self._ontology.get_version()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If mediator exits due to an EDXML validation exception
        # triggered by the EDXML writer, we will not flush the event
        # output buffer. We do that to prevent us from outputting
        # invalid EDXML data. For other kinds of exceptions, like
        # KeyboardInterrupt, flushing the# output buffers is fine.
        self.close(flush=exc_type != EDXMLValidationError)

    @staticmethod
    def _transcoder_is_postprocessor(transcoder):
        this_method = getattr(transcoder, 'post_process')
        base_method = getattr(Transcoder, 'post_process')
        return this_method.__func__ is not base_method.__func__

    @classmethod
    def register(cls, record_selector, record_transcoder):
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
          record_selector: Record type selector
          record_transcoder (class): Transcoder class
        """
        if record_selector in cls.__record_transcoders:
            raise Exception(
                "Attempt to register multiple transcoders for record selector '%s'" % record_selector
            )

        if record_transcoder not in cls.__transcoders:
            cls.__transcoders[record_transcoder] = record_transcoder()
            cls.__auto_merge_eventtypes.extend(
                cls.__transcoders[record_transcoder].get_auto_merge_event_types())

        cls.__record_transcoders[record_selector] = record_transcoder

    def debug(self, disable_buffering=True, warn_no_transcoder=True, warn_fallback=True, log_repaired_events=True):
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
          disable_buffering  (bool): Disable output buffering
          warn_no_transcoder  (bool): Warn when no transcoder found
          warn_fallback      (bool): Warn when using fallback transcoder
          log_repaired_events (bool): Log events that were repaired

        Returns:
          TranscoderMediator:
        """
        self._debug = True
        self.__disable_buffering = disable_buffering
        self._warn_no_transcoder = warn_no_transcoder
        self._warn_fallback = warn_fallback
        self.__log_repaired_events = log_repaired_events

        return self

    def disable_event_validation(self):
        """
        Instructs the EDXML writer not to validate its
        output. This may be used to boost performance in
        case you know that the data will be validated at
        the receiving end, or in case you know that your
        generator is perfect. :)

        Returns:
         TranscoderMediator:
        """
        self.__validate_events = False
        return self

    def ignore_invalid_objects(self):
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

    def ignore_invalid_events(self, warn=False):
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
          warn (bool): Print warnings or not

        Returns:
          TranscoderMediator:
        """
        self._ignore_invalid_events = True
        self._warn_invalid_events = warn
        return self

    def add_event_source(self, source_uri):
        """

        Adds an EDXML event source definition. If no event sources
        are added, a bogus source will be generated.

        Warning:
          The source URI is used to compute sticky
          hashes. Therefore, adjusting the source URIs of events
          after generating them changes their hashes.

        The mediator will not output the EDXML ontology until
        it receives its first event through the process() method.
        This means that the caller can generate an event source
        'just in time' by inspecting the input record and use this
        method to create the appropriate source definition.

        Returns the created EventSource instance, to allow it to
        be customized.

        Args:
          source_uri (str): An Event Source URI

        Returns:
          EventSource:
        """
        source = self._ontology.create_event_source(source_uri)
        self.__sources.append(source)
        return source

    def set_event_source(self, source_uri):
        """

        Set the event source for the output events. This source will
        automatically be set on every output event.

        Args:
          source_uri (str): The event source URI

        Returns:
          TranscoderMediator:
        """
        self._output_source_uri = source_uri
        return self

    @classmethod
    def _get_transcoder(cls, record_selector):
        """

        Returns a Transcoder instance for transcoding
        records matching specified selector, or None if no transcoder
        has been registered for records of that selector.

        Args:
          record_selector (str): record type selector

        Returns:
          Transcoder:
        """

        if record_selector in cls.__record_transcoders:
            return cls.__transcoders[cls.__record_transcoders[record_selector]]
        else:
            return cls.__transcoders.get(cls.__record_transcoders.get('RECORD_OF_UNKNOWN_TYPE'))

    def _write_initial_ontology(self):
        # Here, we write the ontology elements that are
        # defined by the various transcoders.

        # First, we accumulate the object types into an
        # empty ontology.
        object_types = Ontology()
        for transcoder in self.__transcoders.values():
            transcoder.set_ontology(object_types)
            for _ in transcoder.generate_object_types():
                # Here, we only populate the list of object types,
                # we don't do anything with them.
                pass

        # Add the object types to the main mediator ontology
        self._ontology.update(object_types)

        # Then, we accumulate the concepts into an
        # empty ontology.
        concepts = Ontology()
        for transcoder in self.__transcoders.values():
            transcoder.set_ontology(concepts)
            for _ in transcoder.generate_concepts():
                # Here, we only populate the list of concepts,
                # we don't do anything with them.
                pass

        # Add the concepts to the main mediator ontology
        self._ontology.update(concepts)

        # Now, we allow each of the transcoders to create their event
        # types in separate ontologies. We do that to allow two transcoders
        # to create two event types that share the same name. That is
        # a common pattern in transcoders that inherit event type definitions
        # from their parent, adjust the event type and finally rename it.
        for transcoder in self.__transcoders.values():
            transcoder.set_ontology(Ontology())
            transcoder.update_ontology(object_types, validate=False)
            transcoder.update_ontology(concepts, validate=False)
            for _, _ in transcoder.generate_event_types():
                # Here, we only populate the ontology, we
                # don't do anything with the ontology elements.
                self._ontology.update(transcoder._ontology, validate=False)
                transcoder.update_ontology(object_types, validate=False)
                transcoder.update_ontology(concepts, validate=False)
                transcoder.set_ontology(Ontology())

        if len(self.__sources) == 0:
            self.warning(
                'No EDXML source was defined, generating bogus source.')
            self.__sources.append(
                self._ontology.create_event_source('/undefined/'))

        self._writer.add_ontology(self._ontology)
        self._last_written_ontology_version = self._ontology.get_version()

    def _write_ontology_update(self):
        # Here, we write ontology updates resulting
        # from adding new ontology elements while
        # generating events. Currently, this is limited
        # to event source definitions.
        return self._writer.add_ontology(self._ontology)

    def _create_writer(self):
        self._writer = SimpleEDXMLWriter(self.__output, self.__validate_events)
        if self.__disable_buffering:
            self._writer.set_buffer_size(0)
        if self._ignore_invalid_objects:
            self._writer.ignore_invalid_objects()
        if self._ignore_invalid_events:
            self._writer.ignore_invalid_events(self._warn_invalid_events)
        if self.__log_repaired_events:
            self._writer.log_repaired_events()
        for EventTypeName in self.__auto_merge_eventtypes:
            self._writer.auto_merge(EventTypeName)

    def process(self, record):
        """
        Processes a single input record, invoking the correct
        transcoder to generate an EDXML event and writing the
        event into the output.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as unicode string.

        Args:
          record: Input data record

        Returns:
          unicode: Generated output XML data

        """
        return u''

    def close(self, flush=True):
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
        if self._writer is None:
            # Apparently, no events were generated. We will only
            # output the ontology.
            self._create_writer()
            self._write_initial_ontology()

        return self._writer.close(flush)
