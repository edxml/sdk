from edxml.transcode.object import ObjectTranscoder


class UserTranscoder(ObjectTranscoder):
    TYPE_MAP = {'user': 'test-event-type'}
    PROPERTY_MAP = {'test-event-type': {'name': 'user.name'}}

    def create_object_types(self):
        self._ontology.create_object_type('my.object.type')


class UserRecord:
    name = 'Alice'


# Create a transcoder and an input record
transcoder = UserTranscoder()
record = UserRecord()

# Generate output events
events = list(transcoder.generate(record, record_selector='user'))
