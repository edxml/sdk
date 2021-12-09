import os

from edxml import EDXMLPullParser


class MyParser(EDXMLPullParser):
    def _parsed_event(self, event):
        # Do whatever you want here
        ...

    def _parsed_ontology(self, ontology):
        # Do whatever you want here
        ...


with MyParser() as parser:
    parser.parse(os.path.dirname(__file__) + '/input.edxml')
