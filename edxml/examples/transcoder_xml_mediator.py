import sys
from io import BytesIO

from edxml.transcode.xml import XmlTranscoder, XmlTranscoderMediator

xml = bytes(
    '<records>'
    '  <users>'
    '    <user>'
    '      <name>Alice</name>'
    '    </user>'
    '  </users>'
    '</records>', encoding='utf-8'
)


class UserTranscoder(XmlTranscoder):
    TYPES = ['test-event-type']
    TYPE_MAP = {'user': 'test-event-type'}
    TYPE_PROPERTIES = {'test-event-type': {'user.name': 'my.object.type'}}
    PROPERTY_MAP = {'test-event-type': {'name': 'user.name'}}

    def create_object_types(self):
        self._ontology.create_object_type('my.object.type')


# Create a transcoder
transcoder = UserTranscoder()

with XmlTranscoderMediator(output=sys.stdout.buffer) as mediator:
    # Register transcoder
    mediator.register('users', UserTranscoder())
    # Define an EDXML event source
    mediator.add_event_source('/test/uri/')
    # Set the source as current source for all output events
    mediator.set_event_source('/test/uri/')
    # Parse the XML data
    mediator.parse(BytesIO(xml))
