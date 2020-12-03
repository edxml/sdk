# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

import sys
import json

from dateutil.parser import parse

from edxml import EDXMLWriter, EDXMLEvent
from edxml.ontology import Ontology

myOntology = Ontology()

# ...add event type definitions here...

writer = EDXMLWriter(sys.stdout)
writer.add_ontology(myOntology)

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
        writer.add_ontology(myOntology)

    writer.add_event(EDXMLEvent(properties))

writer.close()
