import sys
import json

from dateutil.parser import parse

from edxml import SimpleEDXMLWriter, EDXMLEvent
from edxml.ontology import Ontology

myOntology = Ontology()

# ...add event type definitions here...

writer = SimpleEDXMLWriter(sys.stdout)
writer.set_ontology(myOntology)

definedUri = []

for line in sys.stdin:
    properties = json.loads(line)

    parsedDateTime = parse(properties['datetime'])
    sourceUri = '/some/namespace/' + parsedDateTime.strftime('%Y/%m/')

    if sourceUri not in definedUri:
        # We have not defined this source URI yet.
        sourceDesc = parsedDateTime.strftime('Data generated in %B %Y')
        acquisitionDate = parsedDateTime.strftime('%Y%m%d')
        myOntology.create_event_source(sourceUri, description=sourceDesc, acquisition_date=acquisitionDate)
        definedUri.append(sourceUri)

    writer.add_event(EDXMLEvent(properties))

writer.close()
