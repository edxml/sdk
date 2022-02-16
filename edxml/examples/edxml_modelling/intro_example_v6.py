from edxml.ontology import EventTypeFactory

from edxml_bricks.generic import GenericBrick
from edxml_bricks.computing.files import FilesBrick
from edxml_bricks.computing.generic import ComputingBrick
from edxml_bricks.computing.networking.generic import NetworkingBrick


class FtpTypeFactory(EventTypeFactory):

    TYPES = ['org.myorganization.logs.ftp']

    TYPE_PROPERTIES = {
        'org.myorganization.logs.ftp': {
            'time': GenericBrick.OBJECT_DATETIME,
            'user': ComputingBrick.OBJECT_USER_NAME,
            'command': GenericBrick.OBJECT_STRING_UTF8,
            'server': NetworkingBrick.OBJECT_HOST_IPV4,
            'client': NetworkingBrick.OBJECT_HOST_IPV4,
            'file': FilesBrick.OBJECT_FILE_PATH,
            'offset': GenericBrick.OBJECT_SEQUENCE,
        }
    }

    TYPE_STORIES = {
        'org.myorganization.logs.ftp':
            'On [[date_time:time,second]], a user named "[[user]]" issued '
            'command "[[command]]" on FTP server [[server]]. The command '
            'was issued from a device having IP address [[client]] and was'
            'originally logged in [[file]] at offset [[offset]].'
    }

    TYPE_HASHED_PROPERTIES = {
        'org.myorganization.logs.ftp': ['file', 'offset']
    }

    TYPE_SEQUENCES = {
        'org.myorganization.logs.ftp': 'offset'
    }

    TYPE_PROPERTY_CONCEPTS = {
        'org.myorganization.logs.ftp': {
            'user': {ComputingBrick.CONCEPT_USER_ACCOUNT: 10},
            'server': {ComputingBrick.CONCEPT_COMPUTER: 8},
            'client': {ComputingBrick.CONCEPT_COMPUTER: 8},
        }
    }

    @classmethod
    def create_event_type(cls, event_type_name, ontology):
        ftp = super().create_event_type(event_type_name, ontology)

        ftp['server'].relate_inter('serves', 'client').because(
            'FTP logs show [[client]] executing commands on [[server]]')
