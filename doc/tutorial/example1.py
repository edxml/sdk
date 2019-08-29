from edxml.ontology import Ontology
from edxml.ontology import DataType
import sys
from edxml import SimpleEDXMLWriter, EDXMLEvent
import json
from dateutil.parser import parse

ontology = Ontology()

ontology.create_object_type('datetime') \
    .set_description('date and time in ISO 8601 format')\
    .set_data_type(DataType.datetime())\
    .set_display_name('time stamp')

ontology.create_object_type('computing.networking.host.ipv4') \
    .set_description('IPv4 address of a computer in a computer network')\
    .set_data_type(DataType.ip_v4())\
    .set_display_name('IPv4 address', 'IPv4 addresses')

ontology.create_object_type('computing.user.name') \
    .set_description('name of a computer user account')\
    .set_data_type(DataType.string(length=255))\
    .set_display_name('user name')\
    .fuzzy_match_phonetic()

ontology.create_object_type('computing.ftp.command') \
    .set_description('command issued by means of a File Transfer Protocol')\
    .set_data_type(DataType.string(length=255))\
    .set_display_name('FTP command')

event_type = ontology.create_event_type('org.myorganization.logs.ftp') \
    .set_display_name('FTP command')\
    .set_description('a logged FTP command')\
    .set_summary_template('FTP command issued to [[server]]')\
    .set_story_template(
    'On [[FULLDATETIME:time]], a user named "[[user]]" issued '
    'command "[[command]]" on FTP server [[server]]. The command '
    'was issued from a device having IP address [[client]].')

event_type.create_property('time', 'datetime')
event_type.create_property('server', 'computing.networking.host.ipv4')
event_type.create_property('client', 'computing.networking.host.ipv4')
event_type.create_property('user', 'computing.user.name')
event_type.create_property('command', 'computing.ftp.command')

source = ontology.create_event_source('/myorganization/logs/ftp/')

writer = SimpleEDXMLWriter(sys.stdout)
writer.set_ontology(ontology)

for line in sys.stdin:
    properties = json.loads(line)

    # Delete unused JSON fields
    del properties['source']
    del properties['offset']

    # Convert time to valid EDXML datetime string
    properties['datetime'] = DataType.format_utc_datetime(
        parse(properties['datetime']))

    writer.add_event(
        EDXMLEvent(
            properties,
            event_type_name='org.myorganization.logs.ftp',
            source_uri='/myorganization/logs/ftp/'
        )
    )

writer.close()
