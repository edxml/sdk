from edxml.ontology import Ontology
from edxml.ontology import DataType
import sys
from edxml import SimpleEDXMLWriter, EDXMLEvent
import json
from dateutil.parser import parse

myOntology = Ontology()

myOntology.CreateObjectType('datetime')\
    .SetDescription('date and time in ISO 8601 format')\
    .SetDataType(DataType.DateTime())\
    .SetDisplayName('time stamp')

myOntology.CreateObjectType('computing.networking.host.ipv4')\
    .SetDescription('IPv4 address of a computer in a computer network')\
    .SetDataType(DataType.Ipv4())\
    .SetDisplayName('IPv4 address', 'IPv4 addresses')

myOntology.CreateObjectType('computing.user.name')\
    .SetDescription('name of a computer user account')\
    .SetDataType(DataType.String(Length=255))\
    .SetDisplayName('user name')\
    .FuzzyMatchPhonetic()

myOntology.CreateObjectType('computing.ftp.command')\
    .SetDescription('command issued by means of a File Transfer Protocol')\
    .SetDataType(DataType.String(Length=255))\
    .SetDisplayName('FTP command')

myEventType = myOntology.CreateEventType('org.myorganization.logs.ftp')\
    .SetDisplayName('FTP command')\
    .SetDescription('a logged FTP command')\
    .SetSummaryTemplate('FTP command issued to [[server]]')\
    .SetStoryTemplate(
    'On [[FULLDATETIME:time]], a user named "[[user]]" issued '
    'command "[[command]]" on FTP server [[server]]. The command '
    'was issued from a device having IP address [[client]].')

myEventType.CreateProperty('time', ObjectTypeName='datetime')
myEventType.CreateProperty(
    'server', ObjectTypeName='computing.networking.host.ipv4')
myEventType.CreateProperty(
    'client', ObjectTypeName='computing.networking.host.ipv4')
myEventType.CreateProperty('user', ObjectTypeName='computing.user.name')
myEventType.CreateProperty('command', ObjectTypeName='computing.ftp.command')

mySource = myOntology.CreateEventSource('/myorganization/logs/ftp/')

writer = SimpleEDXMLWriter(sys.stdout)
writer.SetOntology(myOntology)
writer.SetEventType('org.myorganization.logs.ftp')
writer.SetEventSource('/myorganization/logs/ftp/')

for line in sys.stdin:
    properties = json.loads(line)

    # Delete unused JSON fields
    del properties['source']
    del properties['offset']

    # Convert time to valid EDXML datetime string
    properties['datetime'] = DataType.FormatUtcDateTime(
        parse(properties['datetime']))

    writer.AddEvent(EDXMLEvent(properties))

writer.Close()
