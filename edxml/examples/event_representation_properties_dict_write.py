from edxml import EDXMLEvent

# Create an event
event = EDXMLEvent()

# Assign properties in one go
event.properties = {'names': {'Alice', 'Bob'}}

# Single values are wrapped into a set automatically
event.properties['names'] = 'Alice'

# The above could be shortened like this:
event['names'] = 'Alice'

# Add an object value
event['names'].add('Bob')

# Clear property
del event['names']
