from .intro_example_v1 import FtpTypeFactory
from edxml import EDXMLWriter

ontology = FtpTypeFactory().generate_ontology()

EDXMLWriter().add_ontology(ontology).close()
