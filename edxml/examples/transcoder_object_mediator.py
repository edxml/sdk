import sys

from edxml.transcode.object import ObjectTranscoder, ObjectTranscoderMediator
from edxml_bricks.computing.generic import ComputingBrick


class UserTranscoder(ObjectTranscoder):
    TYPES = ['com.acme.staff.account']
    TYPE_MAP = {'user': 'com.acme.staff.account'}
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


class MyMediator(ObjectTranscoderMediator):
    TYPE_FIELD = 'type'


class Record:
    type = 'user'
    name = 'Alice'


with MyMediator(output=sys.stdout.buffer) as mediator:
    # Register the transcoder
    mediator.register('user', UserTranscoder())
    # Define an EDXML event source
    mediator.add_event_source('/acme/offices/amsterdam/')
    # Set the source as current source for all output events
    mediator.set_event_source('/acme/offices/amsterdam/')
    # Process the input record
    mediator.process(Record)
