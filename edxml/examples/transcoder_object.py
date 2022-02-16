from edxml.transcode.object import ObjectTranscoder
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
