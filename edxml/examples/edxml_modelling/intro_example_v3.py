from edxml.ontology import EventTypeFactory

from edxml_bricks.generic import GenericBrick
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
        }
    }

    TYPE_STORIES = {
        'org.myorganization.logs.ftp':
            'On [[date_time:time,second]], a user named "[[user]]" issued '
            'command "[[command]]" on FTP server [[server]]. The command '
            'was issued from a device having IP address [[client]].'
    }
