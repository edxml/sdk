import sys
from io import BytesIO

from edxml.transcode.xml import XmlTranscoder, XmlTranscoderMediator
from edxml_bricks.computing.generic import ComputingBrick

# Define an input document
xml = bytes(
    '<records>'
    '  <users>'
    '    <user>'
    '      <name>Alice</name>'
    '    </user>'
    '  </users>'
    '</records>', encoding='utf-8'
)


# Define a transcoder for user records
class UserTranscoder(XmlTranscoder):
    TYPES = ['com.acme.staff.account']
    TYPE_MAP = {'.': 'com.acme.staff.account'}
    PROPERTY_MAP = {
        'com.acme.staff.account': {
            'name': 'user.name'
        }
    }
    TYPE_PROPERTIES = {
        'com.acme.staff.account': {
            'user.name': ComputingBrick.OBJECT_USER_NAME
        }
    }


# Transcode the input document
with XmlTranscoderMediator(output=sys.stdout.buffer) as mediator:
    # Register transcoder
    mediator.register('/records/users/user', UserTranscoder())
    # Define an EDXML event source
    mediator.add_event_source('/acme/offices/amsterdam/')
    # Set the source as current source for all output events
    mediator.set_event_source('/acme/offices/amsterdam/')
    # Parse the XML data
    mediator.parse(BytesIO(xml))
