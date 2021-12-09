import sys

from edxml.transcode.object import ObjectTranscoder, ObjectTranscoderMediator


class UserTranscoder(ObjectTranscoder):
    TYPES = ['test-event-type']
    TYPE_MAP = {'user': 'test-event-type'}
    TYPE_PROPERTIES = {'test-event-type': {'user.name': 'my.object.type'}}
    PROPERTY_MAP = {'test-event-type': {'name': 'user.name'}}

    def create_object_types(self):
        self._ontology.create_object_type('my.object.type')


class MyMediator(ObjectTranscoderMediator):
    TYPE_FIELD = 'type'


class Record:
    type = 'user'
    name = 'Alice'


# Create a transcoder and an input record
transcoder = UserTranscoder()
record = Record()

with MyMediator(output=sys.stdout.buffer) as mediator:
    # Register the transcoder
    mediator.register('user', transcoder)
    # Define an EDXML event source
    mediator.add_event_source('/test/uri/')
    # Set the source as current source for all output events
    mediator.set_event_source('/test/uri/')
    # Process the input record
    mediator.process(record)
