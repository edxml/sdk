from edxml.ontology import EventTypeFactory
from edxml_bricks.generic import GenericBrick


class FtpTypeFactory(EventTypeFactory):

    TYPES = ['org.myorganization.logs.ftp']

    TYPE_PROPERTIES = {
        'org.myorganization.logs.ftp': {
            'time': GenericBrick.OBJECT_DATETIME
        }
    }
