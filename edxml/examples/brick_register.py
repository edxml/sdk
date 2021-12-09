from edxml.ontology import Brick, Ontology


# Define an ontology brick
class MyBrick(Brick):
    @classmethod
    def generate_object_types(cls, target_ontology):
        yield target_ontology.create_object_type('my.object.type')


# Register brick with Ontology class
Ontology.register_brick(MyBrick)

# Now we can refer to the object type in the brick
ontology = Ontology()
event_type = ontology.create_event_type('my.event.type')
event_type.create_property('prop', object_type_name='my.object.type')
