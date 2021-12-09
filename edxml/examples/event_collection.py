import os

from edxml import EventCollection

data = open(os.path.dirname(__file__) + '/input.edxml', 'rb').read()

collection = EventCollection.from_edxml(data)

for event in collection:
    print(event)
