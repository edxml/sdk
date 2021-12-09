from edxml import EDXMLEvent

# Create an event
event = EDXMLEvent(properties={'names': {'Alice'}})

# Add a 'document' attachment with its SHA1 hash as ID
event.attachments['document'] = 'FooBar'

# Add a 'document' attachment while explicitly setting its ID
event.attachments['document'] = {'1': 'FooBar'}
