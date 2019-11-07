from edxml import EventCollection, EDXMLPushParser
from edxml.transcode import TranscoderMediator


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
        self._event_set = event_set
        super().__init__()

    def write(self, edxml_data):
        self.feed(edxml_data)

    def _parsed_event(self, event):
        self._event_set.append(event)


class TranscoderTestHarness(TranscoderMediator):
    """
    This class is a substitute for the transcoder mediators which can be
    used to test transcoders. It provides the means to feed input records
    to transcoders and make assertions about the output events.
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

        The event is also written into an EDXML writer, which
        triggers all validation that would be applied to the
        event when using a regular transcoder mediator. Note
        that each output event is written into a fresh instance
        of the EDXML writer, producing a full EDXML
        representation for each individual event.

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
