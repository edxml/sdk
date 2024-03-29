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

import logging

import edxml
from edxml import EventCollection, EDXMLPushParser
from edxml.error import EDXMLOntologyValidationError, EDXMLEventValidationError
from edxml.event_validator import EventValidator
from edxml.transcode import TranscoderMediator


logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())


class TestHarnessParser(EDXMLPushParser):
    """
    This parser is used to capture the output of the
    EDXML writer and parse it back to event instances.
    To this end, it implements a write() method, allowing
    it to be used as a file-like output.
    This allows unit tests to verify the output of the
    writer rather than the output of the record transcoder.

    The parsed events are added to an EventCollection
    instance, the content of which can be inspected to
    verify which events were output by the writer.
    """
    def __init__(self, event_set):
        self._event_set = event_set  # type: edxml.EventCollection
        super().__init__()

    def write(self, edxml_data):
        self.feed(edxml_data)

    def _parsed_ontology(self, ontology):
        self._event_set.update_ontology(ontology)

    def _parsed_event(self, event):
        self._event_set.append(event)


class TranscoderTestHarness(TranscoderMediator):
    """
    This class is a substitute for the transcoding mediators which can be
    used to test record transcoders. It provides the means to feed input records
    to record transcoders and make assertions about the output events.

    After processing is completed, either by closing the context or by
    explicitly calling close(), any colliding events are merged. This
    means that unit tests will also test the merging logic of the events.
    """

    def __init__(self, transcoder, record_selector, base_ontology=None, register=True):
        """
        Creates a new test harness for testing specified record transcoder.
        Optionally a base ontology can be provided. When provided,
        the harness will try to upgrade the base ontology to the
        ontology generated by the record transcoder, raising an exception
        in case of backward incompatibilities.

        By default the record transcoder will be automatically registered at
        the specified selector. In case you wish to do the record registration
        on your own you must set the register parameter to False.

        Args:
            transcoder (edxml.transcode.RecordTranscoder): The record transcoder under test
            record_selector (str): Record type selector
            base_ontology (edxml.ontology.Ontology): Base ontology
            register (bool): Register the transcoder yes or no
        """
        self._base_ontology = base_ontology
        self.events: edxml.EventCollection = EventCollection()  #: The resulting event collection
        parser = TestHarnessParser(self.events)
        # Below we use the parser as output of the mediator. The
        # parser will populate self.events.
        super().__init__(output=parser)
        self.transcoder = transcoder
        self.add_event_source('/test/harness/')
        self.set_event_source('/test/harness/')
        if register:
            self.register(record_selector, transcoder)

    def process(self, record, selector=None):
        """
        Processes a single record, invoking the correct record
        transcoder to generate an EDXML event and adding
        the event to the event set.

        The event is also written into an EDXML writer and parsed
        back to an event object. This means that all validation
        that would be applied to the event when using the real
        transcoder mediator has been applied.

        Args:
          record: The input record
          selector: The selector that matched the record
        """

        super().process(record)

        for event in self.transcoder.generate(record, selector):
            if self._output_source_uri:
                event.set_source(self._output_source_uri)

            if self._transcoder_is_postprocessor(self.transcoder):
                for post_processed_event in self._post_process(selector, record, self.transcoder, event):
                    self._write_event(selector, record, post_processed_event)
            else:
                self._write_event(selector, record, event)

    def close(self, write_ontology_update=True):
        super().close(write_ontology_update)
        self.events = self.events.resolve_collisions()  # type: edxml.EventCollection

        # Collision resolution may result in invalid events. So we
        # do another validation round here.
        validator = EventValidator(self.events.ontology)
        for event in self.events:
            if not validator.is_valid(event):
                exception = validator.get_last_error().exception
                raise EDXMLEventValidationError(
                    'Event collision resolution yielded an invalid event:' + str(exception)
                )

        if self._base_ontology:
            # Compare base ontology using the ontology
            # generated by the record transcoder. This will
            # raise an exception when the two are not mutually
            # compatible.
            try:
                self._base_ontology.validate()
            except EDXMLOntologyValidationError as e:
                raise EDXMLOntologyValidationError(
                    'The base ontology provided to the test harness is not valid: ' + str(e)
                )

            try:
                self._base_ontology.__cmp__(self.events.ontology)
            except EDXMLOntologyValidationError as e:
                raise EDXMLOntologyValidationError(
                    'The ontology generated by the record transcoder is not compatible '
                    'with the provided base ontology: ' + str(e)
                )
