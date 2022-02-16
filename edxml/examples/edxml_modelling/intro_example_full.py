import json

from edxml import EDXMLWriter, EDXMLEvent
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

    TYPE_ATTACHMENTS = {
        'org.myorganization.logs.ftp': ['original']
    }

    TYPE_ATTACHMENT_DISPLAY_NAMES = {
        'org.myorganization.logs.ftp': {'original': ['original JSON record']}
    }

    TYPE_ATTACHMENT_MEDIA_TYPES = {
        'org.myorganization.logs.ftp': {'original': 'application/json'}
    }

    @classmethod
    def create_event_type(cls, event_type_name, ontology):
        ftp = super().create_event_type(event_type_name, ontology)

        ftp['server'].relate_inter('serves', 'client').because(
            'FTP logs show [[client]] executing commands on [[server]]')


ontology = FtpTypeFactory().generate_ontology()

ontology.create_event_source(
    uri='/some/example/uri/',
    description='An example'
)

record = '{'
'    "time":    2016-10-11T21:04:36.167,'
'    "source":  "/var/log/ftp/command.4234.log",'
'    "offset":  37873,'
'    "server":  "192.168.1.20",'
'    "client":  "192.168.10.43",'
'    "user":    "alice",'
'    "command": "quit"'
'}'

record_json = json.loads(record)

event = EDXMLEvent(
    properties={
        "time":    record_json['time'],
        "file":    "/var/log/ftp/command.4234.log",
        "offset":  "37873",
        "server":  "192.168.1.20",
        "client":  "192.168.10.43",
        "user":    "alice",
        "command": "quit"
    },
    event_type_name='org.myorganization.logs.ftp',
    source_uri='/some/example/uri/',
    attachments={
        'original': record
    }
)

EDXMLWriter().add_ontology(ontology).add_event(event).close()
