from edxml import EDXMLWriter, EDXMLEvent
from edxml.ontology import Ontology

# Create basic ontology
ontology = Ontology()
ontology.create_object_type(name='some.object.type')
source = ontology.create_event_source(uri='/some/source/')
event_type = ontology.create_event_type(name='some.event.type')
event_type.create_property(name='prop', object_type_name='some.object.type')

# Create an EDXML event
event = EDXMLEvent(
    properties={'prop': {'FooBar'}},
    event_type_name=event_type.get_name(),
    source_uri=source.get_uri()
)

# Generate EDXML data (writes to stdout)
with EDXMLWriter() as writer:
    writer.add_ontology(ontology)
    writer.add_event(event)
