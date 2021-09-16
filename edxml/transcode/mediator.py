# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

from typing import Dict, Optional
from graphviz import Digraph

import edxml
from edxml.logger import log
from edxml.transcode import RecordTranscoder
from edxml.ontology import Ontology
from edxml.ontology.visualization import generate_graph_property_concepts
from edxml.ontology.description import describe_producer_rst
from edxml.error import EDXMLValidationError
from edxml.writer import EDXMLWriter


class TranscoderMediator(object):
    """
    Base class for implementing mediators between a non-EDXML input data source
    and a set of RecordTranscoder implementations that can transcode the input data records
    into EDXML events.

    Sources can instantiate the mediator and feed it input data records, while
    record transcoders can register themselves with the mediator in order to
    transcode the types of input record that they support.

    The class is a Python context manager which will automatically flush the
    output buffer when the mediator goes out of scope.
    """

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

        super().__init__()
        self._debug = False
        self._warn_no_transcoder = False
        self._warn_fallback = False
        self._warn_invalid_events = False
        self._warn_on_post_process_exceptions = True
        self.__allow_repair_drop = {}
        self._ignore_invalid_events = False
        self._ignore_post_process_exceptions = False
        self._output_source_uri = None

        self._num_input_records_processed = 0

        self.__validate_events = True
        self.__allow_repair_normalize = {}
        self.__log_repaired_events = False

        self.__transcoders = {}              # type: Dict[any, edxml.transcode.RecordTranscoder]

        self.__closed = False
        self.__output = output
        self.__writer = None   # type: Optional[edxml.EDXMLWriter]

        self.__ontology = Ontology()

        self._ontology_populated = False
        self._last_written_ontology_version = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close(write_ontology_update=exc_type is None)

    @property
    def _writer(self):
        """
        Property containing the EDXML writer that
        is used to produce output. It will automatically
        output the initial ontology on first access.

        Returns:
            edxml.EDXMLWriter

        """
        if not self.__writer:
            self._create_writer()

        return self.__writer

    @property
    def _ontology(self):
        """
        Property containing the EDXML ontology that
        is used to store all ontology information from
        the registered record transcoders.

        Returns:
            Ontology
        """
        self._populate_ontology()
        return self.__ontology

    @staticmethod
    def _transcoder_is_postprocessor(transcoder):
        this_method = getattr(type(transcoder), 'post_process')
        base_method = getattr(RecordTranscoder, 'post_process')
        return this_method != base_method

    def register(self, record_selector, record_transcoder):
        """

        Register a record transcoder for processing records identified by
        the specified record selector. The exact nature of the record
        selector depends on the mediator implementation.

        The same record transcoder can be registered for multiple
        record selectors.

        Note:
          Any record transcoder that registers itself as a transcoder using None
          as selector is used as the fallback record transcoder. The fallback
          record transcoder is used to transcode any record for which no transcoder
          has been registered.

        Args:
          record_selector: Record type selector
          record_transcoder (edxml.transcode.RecordTranscoder): Record transcoder instance
        """
        if record_selector in self.__transcoders:
            raise Exception(
                "Attempt to register multiple record transcoders for record selector '%s'" % record_selector
            )

        self.__transcoders[record_selector] = record_transcoder

        for event_type_name, property_names in record_transcoder.TYPE_AUTO_REPAIR_NORMALIZE.items():
            self.enable_auto_repair_normalize(event_type_name, property_names)

        for event_type_name, property_names in record_transcoder.TYPE_AUTO_REPAIR_DROP.items():
            self.enable_auto_repair_drop(event_type_name, property_names)

    def debug(self, warn_no_transcoder=True, warn_fallback=True, log_repaired_events=True):
        """
        Enable debugging mode, which prints informative
        messages about transcoding issues, disables
        event buffering and stops on errors.

        Using the keyword arguments, specific debug features
        can be disabled. When warn_no_transcoder is set to False,
        no warnings will be generated when no matching record transcoder
        can be found. When warn_fallback is set to False, no
        warnings will be generated when an input record is routed
        to the fallback transcoder. When log_repaired_events is set
        to False, no message will be generated when an invalid
        event was repaired.

        Args:
          warn_no_transcoder  (bool): Warn when no record transcoder found
          warn_fallback       (bool): Warn when using fallback transcoder
          log_repaired_events (bool): Log events that were repaired

        Returns:
          TranscoderMediator:
        """
        self._debug = True
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

    def enable_auto_repair_drop(self, event_type_name, property_names):
        """

        Allows dropping invalid object values from the specified event
        properties while repairing invalid events. This will only be
        done as a last resort when normalizing object values failed or
        is disabled.

        Note:
          Dropping object values may still lead to invalid events.

        Args:
            event_type_name (str):
            property_names (List[str]):

        Returns:
          TranscoderMediator:
        """
        self.__allow_repair_drop[event_type_name] = property_names

        if self.__writer:
            self.__writer.enable_auto_repair_drop(event_type_name, property_names)

        return self

    def ignore_invalid_events(self, warn=False):
        """

        Instructs the EDXML writer to ignore invalid events.
        After calling this method, any event that fails to
        validate will be dropped. If warn is set to True,
        a detailed warning will be printed, allowing the
        source and cause of the problem to be determined.

        Note:
          If automatic event repair is enabled the writer
          will attempt to repair any invalid events before
          dropping them.

        Note:
          This has no effect when event validation is disabled.

        Args:
          warn (bool): Log warnings or not

        Returns:
          TranscoderMediator:
        """
        self._ignore_invalid_events = True
        self._warn_invalid_events = warn
        return self

    def ignore_post_processing_exceptions(self, warn=True):
        """

        Instructs the mediator to ignore exceptions raised
        by the _post_process() methods of record transcoders.
        After calling this method, any input record that
        that fails transcode due to post processing errors
        will be ignored and a warning is logged. If warn
        is set to False these warnings are suppressed.

        Args:
          warn (bool): Log warnings or not

        Returns:
          TranscoderMediator:
        """
        self._ignore_post_process_exceptions = True
        self._warn_on_post_process_exceptions = warn
        return self

    def enable_auto_repair_normalize(self, event_type_name, property_names):
        """

        Enables automatic repair of the property values of events of
        specified type. Whenever an invalid event is generated by the
        mediator it will try to repair the event by normalizing object
        values of specified properties.

        Args:
            event_type_name (str):
            property_names (List[str]):

        Returns:
            TranscoderMediator
        """
        self.__allow_repair_normalize[event_type_name] = property_names

        if self.__writer:
            self.__writer.enable_auto_repair_normalize(event_type_name, property_names)

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
        return self.__ontology.create_event_source(source_uri)

    def set_event_source(self, source_uri):
        """

        Set a fixed event source for the output events. This source will
        automatically be set on every output event.

        Args:
          source_uri (str): The event source URI

        Returns:
          TranscoderMediator:
        """
        self._output_source_uri = source_uri
        return self

    def _get_transcoder(self, record_selector=None):
        """

        Returns a RecordTranscoder instance for transcoding
        records matching specified selector, or None if no record
        transcoder has been registered for records of that selector.

        Args:
          record_selector (str): record type selector

        Returns:
          Optional[RecordTranscoder]:
        """

        return self.__transcoders.get(record_selector)

    def _populate_ontology(self):

        if self._ontology_populated:
            # Already populated.
            return

        self._ontology_populated = True

        # First, we accumulate the object types into an
        # empty ontology.
        for transcoder in self.__transcoders.values():
            object_types = Ontology()
            transcoder.set_ontology(object_types)
            transcoder.create_object_types()
            # Add the object types to the main mediator ontology
            self.__ontology.update(object_types)

        # Then, we accumulate the concepts into an
        # empty ontology.
        for transcoder in self.__transcoders.values():
            concepts = Ontology()
            transcoder.set_ontology(concepts)
            transcoder.create_concepts()
            # Add the concepts to the main mediator ontology
            self.__ontology.update(concepts)

        # Now, we allow each of the record transcoders to create their event types.
        for transcoder in self.__transcoders.values():
            transcoder.set_ontology(self.__ontology)
            list(transcoder.generate_event_types())

        # Note that below validation also triggers loading of
        # ontology bricks that contain definitions referred to
        # by event types.
        self.__ontology.validate()

    def _write_ontology_update(self):
        if len(self.__ontology.get_event_sources()) == 0:
            log.warning('No EDXML source was defined before writing the first event, generating bogus source.')
            self.__ontology.create_event_source('/undefined/')

        # Here, we write ontology updates resulting
        # from adding new ontology elements while
        # generating events. Currently, this is limited
        # to event source definitions.
        if not self._ontology.is_modified_since(self._last_written_ontology_version):
            # Ontology did not change since we last wrote one.
            return

        self._writer.add_ontology(self._ontology)
        self._last_written_ontology_version = self._ontology.get_version()

    def _create_writer(self):
        self.__writer = EDXMLWriter(
            output=self.__output, validate=self.__validate_events, log_repaired_events=self.__log_repaired_events
        )
        for event_type_name, property_names in self.__allow_repair_drop.items():
            self._writer.enable_auto_repair_drop(event_type_name, property_names)
        if self._ignore_invalid_events:
            self._writer.ignore_invalid_events(self._warn_invalid_events)
        for event_type_name, property_names in self.__allow_repair_normalize.items():
            self._writer.enable_auto_repair_normalize(event_type_name, property_names)
        for event_type_name, property_names in self.__allow_repair_drop.items():
            self._writer.enable_auto_repair_drop(event_type_name, property_names)

    def _write_event(self, record_id, record, event):
        """
        Writes a single event using the EDXML writer.

        Args:
            record_id (str): Record identifier
            event (edxml.EDXMLEvent): The EDXML event
        """
        self._write_ontology_update()

        source_uri = event.get_source_uri()
        if source_uri is None:
            source_uri = self._get_source_uri(record, event)
            if source_uri is None:
                raise Exception(
                    'Failed to assign source URI to output event. Either configure the transcoder mediator to use '
                    'a fixed source URI or override its _get_source_uri() method.'
                )
            event.set_source(source_uri)

        try:
            self._writer.add_event(event)
        except EDXMLValidationError as e:
            if not self._ignore_invalid_events:
                raise
            if self._warn_invalid_events:
                log.warning(
                    'The transcoder for record %s produced '
                    'an invalid event: %s\n\nContinuing...' % (record_id, str(e))
                )

    def _get_source_uri(self, record, event):
        """

        Generates an EDXML source URI for the specified record and the
        EDXML event that was generated from it. This method is invoked by
        the transcoder when no fixed source URI has been configured. It can be
        overridden to implement custom source URI schemas.

        Args:
            record: Input data record
            event (edxml.EDXMLEvent): Generated EDXML event

        Returns:
            str: EDXML source URI
        """
        if self._output_source_uri:
            # We have a fixed source URI
            return self._output_source_uri

    def _transcode(self, record, record_id, record_selector, transcoder):
        """
        Transcodes specified input record and writes the resulting events
        into the configured output. When the record transcoder is the fallback
        transcoder, record_selector will be None.

        Args:
            record: The input record
            record_id (str): Record identifier
            record_selector (Optional[str]): Selector matching the record
            transcoder (edxml.transcode.RecordTranscoder): The record transcoder to use
        """
        for event in transcoder.generate(record, record_selector):
            if self._transcoder_is_postprocessor(transcoder):
                for post_processed_event in self._post_process(record_id, record, transcoder, event):
                    self._write_event(record_id, record, post_processed_event)
            else:
                self._write_event(record_id, record, event)

    def _post_process(self, record_id, record, transcoder, event):
        """
        Uses specified record transcoder to post-process one event, yielding
        zero or more output events.

        Args:
            record_id (str): Record identifier
            record: The input record of the output event
            transcoder (edxml.transcode.RecordTranscoder): The record transcoder to use
            event: The output event

        Yields:
            edxml.EDXMLEvent
        """
        try:
            for post_processed_event in transcoder.post_process(event, record):
                yield post_processed_event
        except Exception as e:
            if not self._ignore_post_process_exceptions:
                raise
            if self._warn_on_post_process_exceptions:
                log.warning(
                    'The post processor of %s failed transcoding record %s: %s\n\nContinuing...' %
                    (type(transcoder).__name__, record_id, str(e))
                )

    def generate_graphviz_concept_relations(self):
        """
        Returns a graph that shows possible concept mining reasoning paths.

        Returns:
            graphviz.Digraph
        """

        graph = Digraph(
            node_attr={'fontname': 'sans', 'shape': 'box', 'style': 'rounded'},
            edge_attr={'fontname': 'sans'},
            graph_attr={'sep': '+8', 'overlap': 'false', 'outputorder': 'edgesfirst', 'splines': 'true'},
            engine='sfdp',
            strict='true'
        )

        generate_graph_property_concepts(self._ontology, graph)
        return graph

    def describe_transcoder(self, input_description):
        """
        Returns a reStructuredText description for a transcoder that
        uses this mediator. This is done by combining the ontologies
        of all registered record transcoders and describing what the
        resulting data would entail.

        Args:
            input_description (str): Short description of the input data

        Returns:
            str
        """

        return describe_producer_rst(self._ontology, 'transcoder', input_description)

    def process(self, record):
        """
        Processes a single input record, invoking the correct
        transcoder to generate an EDXML event and writing the
        event into the output.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Args:
          record: Input data record

        Returns:
          bytes: Generated output XML data

        """
        return b''

    def close(self, write_ontology_update=True):
        """
        Finalizes the transcoding process by flushing
        the output buffer. When the mediator is not used
        as a context manager, this method must be called
        explicitly to properly close the mediator.

        By default the current ontology will be written to the
        output if needed. This can be prevented by using the
        method parameter.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Args:
            write_ontology_update (bool): Output ontology yes/no

        Returns:
          bytes: Generated output XML data

        """
        if self.__closed:
            return b''

        if write_ontology_update:
            # Make sure we output the ontology even
            # when no events are output.
            self._write_ontology_update()

        self._writer.close()
        self.__closed = True

        return self._writer.flush()
