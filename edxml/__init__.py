"""
This package contains the EDXML SDK.
"""
from .version import __version__

from EDXMLWriter import *
from SimpleEDXMLWriter import *
from event import EDXMLEvent, EventElement, ParsedEvent
from EDXMLParser import *
from EDXMLFilter import *

import ontology
import transcode
