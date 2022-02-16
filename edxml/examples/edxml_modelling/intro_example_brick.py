from edxml.ontology import Brick
from edxml.ontology import DataType


class MyOwnBrick(Brick):

    OBJECT_FTP_COMMAND = 'org.myorganization.ftp.command'

    @classmethod
    def generate_object_types(cls, target_ontology):

        yield target_ontology.create_object_type(cls.OBJECT_FTP_COMMAND)\
            .set_description('a command issued on an FTP server')\
            .set_data_type(DataType.string())\
            .set_display_name('FTP command')
