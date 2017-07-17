from edxml.ontology import Ontology

myOntology = Ontology()

from edxml.ontology import DataType

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
  .SetDataType(DataType.String(255))\
  .SetDisplayName('user name')

myEventType = myOntology.CreateEventType('org.myorganization.logs.ftp')\
  .SetDisplayName('FTP command')\
  .SetDescription('a logged FTP command')\
  .SetReporterShort('FTP command issued to [[server]]')\
  .SetReporterLong(
    'On [[FULLDATETIME:time]], a user named "[[user]]" issued '
    'command "[[command]]" on FTP server [[server]]. The command '
    'was issued from a device having IP address [[client]].')

myEventType.CreateProperty('time',    ObjectTypeName='datetime')
myEventType.CreateProperty('server',  ObjectTypeName='computing.networking.host.ipv4')
myEventType.CreateProperty('client',  ObjectTypeName='computing.networking.host.ipv4')
myEventType.CreateProperty('user',    ObjectTypeName='computing.user.name')
myEventType.CreateProperty('command', ObjectTypeName='computing.ftp.command')

mySource = myOntology.CreateEventSource('/myorganization/logs/ftp/')

import sys
from edxml import SimpleEDXMLWriter, EDXMLEvent

writer = SimpleEDXMLWriter(sys.stdout)
writer.SetOntology(myOntology)
writer.SetEventType('org.myorganization.logs.ftp')
writer.SetEventSource('/myorganization/logs/ftp/')

import json

for line in sys.stdin:
  properties = json.loads(line)
  del properties['source']
  del properties['offset']
  writer.AddEvent(EDXMLEvent(properties))

writer.Close()
