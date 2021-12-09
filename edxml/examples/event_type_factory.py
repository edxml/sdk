from edxml.ontology import Ontology, EventTypeFactory


class MyFactory(EventTypeFactory):
    TYPES = ['event-type.a']
    TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'my.object.type'}
    }

    def create_object_types(self):
        self._ontology.create_object_type('my.object.type')


# Create factory and set its ontology
factory = MyFactory().set_ontology(Ontology())

# Create the necessary object types
factory.create_object_types()

# Generate event types
event_types = list(factory.generate_event_types())
