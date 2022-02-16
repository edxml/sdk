from edxml.ontology import EventTypeFactory


class MyFactory(EventTypeFactory):
    TYPES = ['event-type.a']
    TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'my.object.type'}
    }


ontology = MyFactory().generate_ontology()
