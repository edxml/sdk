from edxml import EDXMLEvent

# Create an event
event = EDXMLEvent(properties={'names': {'Alice', 'Bob'}})

for property_name, object_values in event.items():
    for object_value in object_values:
        print(object_value)
