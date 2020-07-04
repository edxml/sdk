import logging

import edxml
from edxml import EventCollection, EDXMLPushParser
from edxml.error import EDXMLValidationError
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
    writer rather than the output of the transcoder.

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
        self._event_set._ontology.update(ontology)

    def _parsed_event(self, event):
        self._event_set.append(event)


class TranscoderTestHarness(TranscoderMediator):
    """
    This class is a substitute for the transcoder mediators which can be
    used to test transcoders. It provides the means to feed input records
    to transcoders and make assertions about the output events.

    After processing is completed, either by closing the context or by
    explicitly calling close(), any colliding events are merged. This
    means that unit tests will also test the merging logic of the events.
    """

    def __init__(self, transcoder):
        """
        Creates a new test harness for testing specified transcoder
        using XML fixtures stored at the indicated path.

        Args:
            transcoder (edxml.transcode.Transcoder): The transcoder under test
        """
        self.events = EventCollection()
        parser = TestHarnessParser(self.events)
        # Below we use the parser as output of the mediator. The
        # parser will populate self.events.
        super(TranscoderTestHarness, self).__init__(output=parser)
        self.transcoder = transcoder

    def process(self, record, selector=None):
        """
        Processes a single record, invoking the correct
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

        for event in self.transcoder.generate(record, selector):
            if self._output_source_uri:
                event.set_source(self._output_source_uri)

            if self._transcoder_is_postprocessor(self.transcoder):
                for post_processed_event in self._post_process(selector, record, self.transcoder, event):
                    self._write_event(selector, post_processed_event)
            else:
                self._write_event(selector, event)

    def close(self, flush=True):
        super().close(flush)
        self.events = self.events.resolve_collisions()
