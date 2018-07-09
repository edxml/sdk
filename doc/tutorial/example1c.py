from edxml.ontology import Ontology
from edxml.ontology import DataType
import sys
import json
from edxml import SimpleEDXMLWriter, EDXMLEvent

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

myOntology.CreateConcept('computer') \
    .SetDescription('some kind of a computing device') \
    .SetDisplayName('computer')

myEventType = myOntology.CreateEventType('org.myorganization.logs.ftp')\
    .SetDisplayName('FTP command')\
    .SetDescription('a logged FTP command')\
    .SetSummaryTemplate('FTP command issued to [[server]]')\
    .SetStoryTemplate(
    'On [[FULLDATETIME:time]], a user named "[[user]]" issued '
    'command "[[command]]" on FTP server [[server]]. The command '
    'was issued from a device having IP address [[client]].')

myEventType.CreateProperty('time',    ObjectTypeName='datetime')
myEventType.CreateProperty(
    'server',  ObjectTypeName='computing.networking.host.ipv4')
myEventType.CreateProperty(
    'client',  ObjectTypeName='computing.networking.host.ipv4')
myEventType.CreateProperty('user',    ObjectTypeName='computing.user.name')
myEventType.CreateProperty('command', ObjectTypeName='computing.ftp.command')

myEventType['user'].RelateTo('has access to', 'server') \
                   .Because('a user named [[user]] issued a command on FTP server [[server]]') \
                   .SetConfidence(10)

myEventType['client'].Identifies('computer', 9)
myEventType['server'].Identifies('computer', 9)

myEventType['client'].RelateIntra('communicates with', 'server') \
    .Because('[[client]] connected to FTP server [[server]]')

mySource = myOntology.CreateEventSource('/myorganization/logs/ftp/')

with SimpleEDXMLWriter(sys.stdout) as writer:
    writer.SetOntology(myOntology)\
          .SetEventType('org.myorganization.logs.ftp')\
          .SetEventSource('/myorganization/logs/ftp/')

    for line in sys.stdin:
        properties = json.loads(line)
        del properties['source']
        del properties['offset']
        writer.AddEvent(EDXMLEvent(properties).SetContent(line))
