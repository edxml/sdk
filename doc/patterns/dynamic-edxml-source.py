import sys
import json

from dateutil.parser import parse

from edxml import SimpleEDXMLWriter, EDXMLEvent
from edxml.ontology import Ontology

myOntology = Ontology()

# ...add event type definitions here...

writer = SimpleEDXMLWriter(sys.stdout)
writer.SetOntology(myOntology)

definedUri = []

for line in sys.stdin:
    properties = json.loads(line)

    parsedDateTime = parse(properties['datetime'])
    sourceUri = '/some/namespace/' + parsedDateTime.strftime('%Y/%m/')

    if sourceUri not in definedUri:
        # We have not defined this source URI yet.
        sourceDesc = parsedDateTime.strftime('Data generated in %B %Y')
        acquisitionDate = parsedDateTime.strftime('%Y%m%d')
        myOntology.CreateEventSource(
            sourceUri, Description=sourceDesc, AcquisitionDate=acquisitionDate)
        definedUri.append(sourceUri)

    writer.AddEvent(EDXMLEvent(properties))

writer.Close()
