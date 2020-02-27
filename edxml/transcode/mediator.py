# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import Dict

import edxml
from edxml.logger import log
from edxml.transcode import Transcoder
from edxml.ontology import Ontology, PropertyRelation
from edxml.error import EDXMLValidationError, EDXMLError
from edxml.SimpleEDXMLWriter import SimpleEDXMLWriter


class TranscoderMediator(object):
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
        self._debug = False
        self._warn_no_transcoder = False
        self._warn_fallback = False
        self._warn_invalid_events = False
        self._warn_on_post_process_exceptions = True
        self._ignore_invalid_objects = False
        self._ignore_invalid_events = False
        self._ignore_post_process_exceptions = False
        self._output_source_uri = None

        self.__disable_buffering = False
        self.__validate_events = True
        self.__log_repaired_events = False

        self.__sources = []
        self.__closed = False
        self.__output = output
        self.__writer = None   # var: edxml.SimpleEDXMLWriter

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

    @property
    def _writer(self):
        """
        Property containing the EDXML writer that
        is used to produce output. It will automatically
        output the initial ontology on first access.

        Returns:
            edxml.SimpleEDXMLWriter

        """
        if not self.__writer:
            self._create_writer()
            self._write_initial_ontology()
        return self.__writer

    @classmethod
    def clear_registrations(cls):
        # TODO: Remove this method as soon as registrations are
        #       no longer kept in class constants.
        cls.__record_transcoders = {}
        cls.__transcoders = {}
        cls.__sources = []

    @staticmethod
    def _transcoder_is_postprocessor(transcoder):
        this_method = getattr(type(transcoder), 'post_process')
        base_method = getattr(Transcoder, 'post_process')
        return this_method != base_method

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
          Any transcoder that registers itself as a transcoder using None
          as selector is used as the fallback transcoder. The fallback
          transcoder is used to transcode any record for which no transcoder
          has been registered.

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
        validate will be dropped. If warn is set to True,
        a detailed warning will be printed, allowing the
        source and cause of the problem to be determined.

        Note:
          This also implies that invalid objects will be
          ignored.

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
        by the _post_process() methods of transcoders.
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
    def _get_transcoder(cls, record_selector=None):
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

    def _prepare_write_event(self):
        if self._ontology.is_modified_since(self._last_written_ontology_version):
            # Ontology was changed since we wrote the last ontology update,
            # so we need to write another update.
            # TODO: Below writes a full ontology, we should only
            #       output any new or updated elements.
            self._write_ontology_update()
            self._last_written_ontology_version = self._ontology.get_version()

    def _write_initial_ontology(self):
        # Here, we write the ontology elements that are
        # defined by the various transcoders.
        self._initialize_ontology(self._ontology)

        if len(self.__sources) == 0:
            log.warning('No EDXML source was defined before writing the first event, generating bogus source.')
            self.__sources.append(self._ontology.create_event_source('/undefined/'))

        self._writer.add_ontology(self._ontology)
        self._last_written_ontology_version = self._ontology.get_version()

    @classmethod
    def _initialize_ontology(cls, ontology):

        # First, we accumulate the object types into an
        # empty ontology.
        object_types = Ontology()
        for transcoder in cls.__transcoders.values():
            transcoder.set_ontology(object_types)
            transcoder.create_object_types()

        # Add the object types to the main mediator ontology
        ontology.update(object_types)

        # Then, we accumulate the concepts into an
        # empty ontology.
        concepts = Ontology()
        for transcoder in cls.__transcoders.values():
            transcoder.set_ontology(concepts)
            transcoder.create_concepts()

        # Add the concepts to the main mediator ontology
        ontology.update(concepts)

        # Now, we allow each of the transcoders to create their event
        # types in separate ontologies. We do that to allow two transcoders
        # to create two event types that share the same name. That is
        # a common pattern in transcoders that inherit event type definitions
        # from their parent, adjust the event type and finally rename it.
        for transcoder in cls.__transcoders.values():
            transcoder.set_ontology(Ontology())
            transcoder.update_ontology(object_types, validate=False)
            transcoder.update_ontology(concepts, validate=False)
            list(transcoder.generate_event_types())
            ontology.update(transcoder._ontology, validate=False)

        return ontology

    def _write_ontology_update(self):
        # Here, we write ontology updates resulting
        # from adding new ontology elements while
        # generating events. Currently, this is limited
        # to event source definitions.
        return self._writer.add_ontology(self._ontology)

    def _create_writer(self):
        self.__writer = SimpleEDXMLWriter(self.__output, self.__validate_events)
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

    def _write_event(self, record_id, event):
        """
        Writes a single event using the EDXML writer.

        If no output was configured for the EDXML writer the
        generated XML data will be returned as bytes.

        Args:
            record_id (str): Record identifier
            event (edxml.EDXMLEvent): The EDXML event

        Returns:
            bytes:
        """
        self._prepare_write_event()

        outputs = []
        try:
            outputs.append(self._writer.add_event(event))
        except StopIteration:
            # This is raised by the coroutine in EDXMLWriter when the
            # coroutine receives a send() after is was closed.
            # TODO: Can this still happen? It looks like every send() and next() is
            #       enclosed in a try / catch that raises RuntimeException.
            outputs.append(self._writer.close())
        except EDXMLError as e:
            if not self._ignore_invalid_events:
                raise
            if self._warn_invalid_events:
                log.warning(
                    'The post processor of the transcoder for record %s produced '
                    'an invalid event: %s\n\nContinuing...' % (record_id, str(e))
                )
        return b''.join(outputs)

    def _transcode(self, record, record_id, record_selector, transcoder):
        """
        Transcodes specified input record and writes the resulting events
        into the configured output. When the transcoder is the fallback
        transcoder, record_selector will be None.

        If no output was configured for the EDXML writer the
        generated XML data will be returned as bytes.

        Args:
            record: The input record
            record_id (str): Record identifier
            record_selector (Optional[str]): Selector matching the record
            transcoder (edxml.transcode.Transcoder): The transcoder to use

        Returns:
            bytes:

        """
        outputs = []

        for event in transcoder.generate(record, record_selector):
            if self._output_source_uri:
                event.set_source(self._output_source_uri)

            if self._transcoder_is_postprocessor(transcoder):
                for post_processed_event in self._post_process(record_id, record, transcoder, event):
                    outputs.append(self._write_event(record_id, post_processed_event))
            else:
                outputs.append(self._write_event(record_id, event))

        return b''.join(outputs)

    def _post_process(self, record_id, record, transcoder, event):
        """
        Uses specified transcoder to post-process one event, yielding
        zero or more output events.

        Args:
            record_id (str): Record identifier
            record: The input record of the output event
            transcoder (edxml.transcode.Transcoder): The transcoder to use
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

    @classmethod
    def describe(cls, source_name):

        ontology = Ontology()
        cls._initialize_ontology(ontology)

        description = f"\n\nThis transcoder reads {source_name} and outputs "\
                      f"`EDXML <http://edxml.org/>`_ containing {cls._describe_event_types(ontology)}.\n"

        relates_inter = cls._describe_inter_concept_relations(ontology)
        relates_intra = cls._describe_intra_concept_relations(ontology)
        concept_refinements = cls._describe_concept_refinements(
            ontology,
            '\n- {concept_source} as {concept_target} (using {event_type})'
        )

        if relates_inter:
            description += '\nThe transcoder enables automatic correlation of\n'
            for source_concept_name, target_concept_names in relates_inter.items():
                for target_concept_name, event_type_names in target_concept_names.items():
                    source_concept_dn = ontology.get_concept(source_concept_name).get_display_name_plural()
                    target_concept_dn = ontology.get_concept(target_concept_name).get_display_name_plural()
                    if source_concept_name == target_concept_name:
                        description += f"\n- Multiple {source_concept_dn} to discover interconnected networks (using "
                    else:
                        description += f"\n- {source_concept_dn.capitalize()} to {target_concept_dn} (using "
                    event_type_dn = []
                    for event_type_name in event_type_names:
                        event_type_dn.append(ontology.get_event_type(event_type_name).get_display_name_plural())
                    description += ', '.join(event_type_dn) + ')'

        if relates_intra:
            description += '\n\nThe transcoder enhances `concept mining <http://edxml.org/concept-mining>`_ ' \
                           'by expanding knowledge about\n'

        for source_concept_name, target_concept_names in relates_intra.items():
            for target_concept_name, object_type_names in target_concept_names.items():
                source_concept_dn = ontology.get_concept(source_concept_name).get_display_name_plural()
                description += f"\n:{source_concept_dn.capitalize()}: Discovering new "
                object_type_dn = []
                for object_type_name in object_type_names:
                    object_type_dn.append(ontology.get_object_type(object_type_name).get_display_name_plural())
                description += ', '.join(object_type_dn)

        if concept_refinements:
            description += '\nThe transcoder identifies\n' + '\n'.join(concept_refinements)

        concepts = cls._describe_concepts(ontology)
        object_types = cls._describe_object_types(ontology)

        description += '\n\nThe output can be auto-correlated with third party data sources that share any of the ' \
                       'concepts and object types generated by this transcoder. These are listed below.'

        if concepts:
            description += '\n\n'
            description += 'Concepts\n'
            description += '--------\n'
            for concept in sorted(concepts):
                description += f"\n- {concept}"

        if object_types:
            description += '\n\n'
            description += 'Object Types\n'
            description += '------------\n'
            for object_type in sorted(object_types):
                description += f"\n- {object_type}"

        return description

    @classmethod
    def _describe_concepts(cls, ontology):
        concept_names = []
        for concept in ontology.get_concepts().values():
            concept_names.append(f"{concept.get_name()} ({concept.get_display_name_singular()})")
        return concept_names

    @classmethod
    def _describe_object_types(cls, ontology):
        object_type_names = []
        for object_type in ontology.get_object_types().values():
            object_type_names.append(f"{object_type.get_name()} ({object_type.get_display_name_singular()})")
        return object_type_names

    @classmethod
    def _describe_event_types(cls, ontology):
        type_names = []
        for event_type_name in ontology.get_event_type_names():
            type_names.append(ontology.get_event_type(event_type_name).get_display_name_plural())
        if len(type_names) > 1:
            last = type_names.pop()
            return ', '.join(type_names) + ' and ' + last
        else:
            return ' and '.join(type_names)

    @classmethod
    def _describe_inter_concept_relations(cls, ontology):
        relations = defaultdict(lambda: defaultdict(set))
        for event_type_name in ontology.get_event_type_names():
            event_type = ontology.get_event_type(event_type_name)
            for relation in event_type.get_property_relations().values():  # type: PropertyRelation
                if relation.get_type() != 'inter':
                    continue
                relations[relation.get_source_concept()][relation.get_target_concept()].add(event_type_name)
        return relations

    @classmethod
    def _describe_intra_concept_relations(cls, ontology):
        relations = defaultdict(lambda: defaultdict(set))
        for event_type_name in ontology.get_event_type_names():
            event_type = ontology.get_event_type(event_type_name)
            for relation in event_type.get_property_relations().values():  # type: PropertyRelation
                if relation.get_type() != 'intra':
                    continue
                relations[relation.get_source_concept()][relation.get_target_concept()].update(
                    {
                        event_type[relation.get_source()].get_object_type_name(),
                        event_type[relation.get_target()].get_object_type_name()
                    }
                )
        return relations

    @classmethod
    def _describe_concept_refinements(cls, ontology, item_template):
        descriptions = []
        for event_type_name in ontology.get_event_type_names():
            event_type = ontology.get_event_type(event_type_name)
            for relation in event_type.get_property_relations().values():  # type: PropertyRelation
                if relation.get_type() != 'intra':
                    continue
                source_concept = ontology.get_concept(relation.get_source_concept())
                target_concept = ontology.get_concept(relation.get_target_concept())
                if source_concept.get_name() == target_concept.get_name():
                    continue
                descriptions.append(
                    item_template.format({
                        'concept_source': source_concept.get_display_name_plural(),
                        'concept_target': target_concept.get_display_name_plural(),
                        'event_type': event_type.get_display_name_plural()
                    })
                )
        return descriptions

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

    def close(self, flush=True):
        """
        Finalizes the transcoding process by flushing
        the output buffer. When the mediator is not used
        as a context manager, this method must be called
        explicitly to properly close the mediator.

        By default, any remaining events in the output buffer will
        be written to the output, unless flush is set to False.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Args:
          flush (bool): Flush output buffer

        Returns:
          bytes: Generated output XML data

        """
        if self.__closed:
            return b''

        if self._writer is None:
            # Apparently, no events were generated. We will only
            # output the ontology.
            self._create_writer()
            self._write_initial_ontology()

        self.__closed = True
        return self._writer.close(flush)
