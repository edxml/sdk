# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import Dict, Optional
from graphviz import Digraph

import edxml
from edxml.logger import log
from edxml.transcode import Transcoder
from edxml.ontology import Ontology, Concept
from edxml.error import EDXMLError
from edxml.EDXMLWriter import EDXMLWriter


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

        self.__transcoders = {}              # type: Dict[any, edxml.transcode.Transcoder]

        self.__closed = False
        self.__output = output
        self.__writer = None   # type: Optional[edxml.EDXMLWriter]

        self.__ontology = Ontology()

        self._ontology_populated = False
        self._last_written_ontology_version = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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
        the registered transcoders.

        Returns:
            Ontology
        """
        self._populate_ontology()
        return self.__ontology

    @staticmethod
    def _transcoder_is_postprocessor(transcoder):
        this_method = getattr(type(transcoder), 'post_process')
        base_method = getattr(Transcoder, 'post_process')
        return this_method != base_method

    def register(self, record_selector, record_transcoder):
        """

        Register a transcoder for processing records identified by
        the specified record selector. The exact nature of the record
        selector depends on the mediator implementation.

        The same transcoder can be registered for multiple
        record selectors.

        Note:
          Any transcoder that registers itself as a transcoder using None
          as selector is used as the fallback transcoder. The fallback
          transcoder is used to transcode any record for which no transcoder
          has been registered.

        Args:
          record_selector: Record type selector
          record_transcoder (edxml.transcode.Transcoder): Transcoder instance
        """
        if record_selector in self.__transcoders:
            raise Exception(
                "Attempt to register multiple transcoders for record selector '%s'" % record_selector
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
        no warnings will be generated when no matching transcoder
        can be found. When warn_fallback is set to False, no
        warnings will be generated when an input record is routed
        to the fallback transcoder. When log_repaired_events is set
        to False, no message will be generated when an invalid
        event was repaired.

        Args:
          warn_no_transcoder  (bool): Warn when no transcoder found
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

        Set the event source for the output events. This source will
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

        Returns a Transcoder instance for transcoding
        records matching specified selector, or None if no transcoder
        has been registered for records of that selector.

        Args:
          record_selector (str): record type selector

        Returns:
          Optional[Transcoder]:
        """

        return self.__transcoders.get(record_selector)

    def _populate_ontology(self):

        if self._ontology_populated:
            # Already populated.
            return

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

        # Now, we allow each of the transcoders to create their event types.
        for transcoder in self.__transcoders.values():
            transcoder.set_ontology(self.__ontology)
            list(transcoder.generate_event_types())

        if len(self.__ontology.get_event_sources()) == 0:
            log.warning('No EDXML source was defined before writing the first event, generating bogus source.')
            self.__ontology.create_event_source('/undefined/')

        # Note that below validation also triggers loading of
        # ontology bricks that contain definitions referred to
        # by event types.
        self.__ontology.validate()

        self._ontology_populated = True

    def _write_ontology_update(self):
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

    def _write_event(self, record_id, event):
        """
        Writes a single event using the EDXML writer.

        Args:
            record_id (str): Record identifier
            event (edxml.EDXMLEvent): The EDXML event
        """
        self._write_ontology_update()

        try:
            self._writer.add_event(event)
        except StopIteration:
            # This is raised by the coroutine in EDXMLWriter when the
            # coroutine receives a send() after is was closed.
            # TODO: Can this still happen? It looks like every send() and next() is
            #       enclosed in a try / catch that raises RuntimeException.
            self._writer.close()
        except EDXMLError as e:
            if not self._ignore_invalid_events:
                raise
            if self._warn_invalid_events:
                log.warning(
                    'The post processor of the transcoder for record %s produced '
                    'an invalid event: %s\n\nContinuing...' % (record_id, str(e))
                )

    def _transcode(self, record, record_id, record_selector, transcoder):
        """
        Transcodes specified input record and writes the resulting events
        into the configured output. When the transcoder is the fallback
        transcoder, record_selector will be None.

        Args:
            record: The input record
            record_id (str): Record identifier
            record_selector (Optional[str]): Selector matching the record
            transcoder (edxml.transcode.Transcoder): The transcoder to use
        """
        for event in transcoder.generate(record, record_selector):
            if self._output_source_uri:
                event.set_source(self._output_source_uri)

            if self._transcoder_is_postprocessor(transcoder):
                for post_processed_event in self._post_process(record_id, record, transcoder, event):
                    self._write_event(record_id, post_processed_event)
            else:
                self._write_event(record_id, event)

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

        self._ontology.generate_graph_property_concepts(graph)
        return graph

    def describe_transcoder(self, source_name):
        """
        Returns a reStructuredText description for a transcoder that
        uses this mediator. This is done by combining the ontologies
        of all registered record transcoders and describing what the
        resulting data would entail.

        Args:
            source_name (str): A description of the data source

        Returns:
            str
        """

        description = f"\n\nThis transcoder reads {source_name} and outputs "\
                      f"`EDXML <http://edxml.org/>`_ containing {self._describe_event_types(self._ontology)}.\n"

        relates_inter = self._describe_inter_concept_relations(self._ontology)
        relates_intra = self._describe_intra_concept_relations(self._ontology)
        concept_combinations = self._describe_concept_specializations(
            self._ontology,
            '- {concept_source} as {concept_target} (using {event_type})'
        )
        concept_combinations.extend(
            self._describe_concept_universals(
                self._ontology,
                '- {concept_source} as {concept_target}'
            )
        )

        if relates_inter:
            description += '\nThe transcoder enables automatic correlation of\n'
            for source_concept_name, target_concept_names in relates_inter.items():
                for target_concept_name, event_type_names in target_concept_names.items():
                    source_concept_dn = self._ontology.get_concept(source_concept_name).get_display_name_plural()
                    target_concept_dn = self._ontology.get_concept(target_concept_name).get_display_name_plural()
                    if source_concept_name == target_concept_name:
                        description += f"\n- Multiple {source_concept_dn} to discover interconnected networks (using "
                    else:
                        description += f"\n- {source_concept_dn.capitalize()} to {target_concept_dn} (using "
                    event_type_dn = []
                    for event_type_name in event_type_names:
                        event_type_dn.append(self._ontology.get_event_type(event_type_name).get_display_name_plural())
                    description += ', '.join(event_type_dn) + ')'

        if relates_intra:
            description += '\n\nThe transcoder enhances `concept mining <http://edxml.org/concept-mining>`_ ' \
                           'by expanding knowledge about\n'

        expansions = defaultdict(set)
        for concept_name, attribute_names in relates_intra.items():
            concept_dn = self._ontology.get_concept(concept_name).get_display_name_plural()
            expansions[concept_dn].update(attribute_names)

        for concept_dn, object_types in expansions.items():
            description += f"\n:{concept_dn.capitalize()}: Discovering new " + ', '.join(object_types)

        if concept_combinations:
            description += '\n\nThe transcoder identifies\n' + '\n'.join(set(concept_combinations))

        concepts = self._describe_concepts(self._ontology)
        object_types = self._describe_object_types(self._ontology)

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
    def _describe_concepts(cls, ontology: Ontology):
        concept_names = []
        for concept in ontology.get_concepts().values():
            concept_names.append(f"{concept.get_name()} ({concept.get_display_name_singular()})")
        return concept_names

    @classmethod
    def _describe_object_types(cls, ontology: Ontology):
        object_type_names = []
        for object_type in ontology.get_object_types().values():
            object_type_names.append(f"{object_type.get_name()} ({object_type.get_display_name_singular()})")
        return object_type_names

    @classmethod
    def _describe_event_types(cls, ontology: Ontology):
        type_names = []
        for event_type_name in ontology.get_event_type_names():
            type_names.append(ontology.get_event_type(event_type_name).get_display_name_plural())
        if len(type_names) > 1:
            last = type_names.pop()
            return ', '.join(type_names) + ' and ' + last
        else:
            return ' and '.join(type_names)

    @classmethod
    def _describe_inter_concept_relations(cls, ontology: Ontology):
        relations = defaultdict(lambda: defaultdict(set))
        for event_type_name in ontology.get_event_type_names():
            event_type = ontology.get_event_type(event_type_name)
            for relation in event_type.relations:
                if relation.get_type() != 'inter':
                    continue
                relations[relation.get_source_concept()][relation.get_target_concept()].add(event_type_name)
        return relations

    @classmethod
    def _describe_intra_concept_relations(cls, ontology: Ontology):
        relations = defaultdict(set)
        for event_type_name in ontology.get_event_type_names():
            event_type = ontology.get_event_type(event_type_name)
            for relation in event_type.relations:
                if relation.get_type() != 'intra':
                    continue
                relations[relation.get_source_concept()].add(
                    event_type[relation.get_source()].get_concept_associations()[relation.get_source_concept()]
                    .get_attribute_display_name_plural(),
                )
                relations[relation.get_target_concept()].add(
                    event_type[relation.get_target()].get_concept_associations()[relation.get_target_concept()]
                    .get_attribute_display_name_plural(),
                )
        return relations

    @classmethod
    def _describe_concept_specializations(cls, ontology: Ontology, item_template):
        descriptions = []
        for event_type_name in ontology.get_event_type_names():
            event_type = ontology.get_event_type(event_type_name)
            for relation in event_type.relations:
                if relation.get_type() != 'intra':
                    continue
                source_concept = ontology.get_concept(relation.get_source_concept())
                target_concept = ontology.get_concept(relation.get_target_concept())
                if source_concept.get_name() == target_concept.get_name():
                    continue
                descriptions.append(
                    item_template.format(**{
                        'concept_source': source_concept.get_display_name_plural(),
                        'concept_target': target_concept.get_display_name_plural(),
                        'event_type': event_type.get_display_name_plural()
                    })
                )

        return descriptions

    @classmethod
    def _describe_concept_universals(cls, ontology: Ontology, item_template):
        descriptions = []
        for concept_name in ontology.get_concept_names():
            # Search for a base concept by traversing all specializations until
            # we find one that exists.
            for parent in Concept.generate_specializations(concept_name):
                # Note that we do not want to import any concepts here, as that
                # may pull in concepts that are not used by the transcoder.
                source_concept = ontology.get_concept(parent, import_brick=False)
                if source_concept is None:
                    continue

                # Search for specializations of the parent name to generate pairs of
                # concepts that are a generalization and a specialization of the base concept.
                # So, given a parent concept of a.b we try to pair it with a.b.c.
                for specialization in Concept.generate_specializations(concept_name, parent):
                    # Note that we do not want to import any concepts here, as that
                    # may pull in concepts that are not used by the transcoder.
                    target_concept = ontology.get_concept(specialization, import_brick=False)
                    if target_concept is None:
                        continue

                    descriptions.append(
                        item_template.format(**{
                            'concept_source': source_concept.get_display_name_plural(),
                            'concept_target': target_concept.get_display_name_plural()
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

    def close(self):
        """
        Finalizes the transcoding process by flushing
        the output buffer. When the mediator is not used
        as a context manager, this method must be called
        explicitly to properly close the mediator.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Returns:
          bytes: Generated output XML data

        """
        if self.__closed:
            return b''

        # Make sure we output the ontology even
        # when no events are output.
        self._write_ontology_update()

        self._writer.close()
        self.__closed = True

        return self._writer.flush()
