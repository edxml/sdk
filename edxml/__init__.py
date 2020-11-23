"""
This package contains the EDXML SDK.
"""
from .version import __version__

from .event import EDXMLEvent, EventElement, ParsedEvent
from .template import Template
from .writer import EDXMLWriter
from .EDXMLParser import EDXMLPullParser, EDXMLPushParser, EDXMLOntologyPullParser, EDXMLOntologyPushParser
from .EDXMLFilter import EDXMLPullFilter, EDXMLPushFilter
from .event_collection import EventCollection

from . import ontology
from . import transcode


__all__ = ['EDXMLEvent', 'EventElement', 'ParsedEvent', 'EventCollection', 'EDXMLWriter',
           'EDXMLPullParser', 'EDXMLPushParser', 'EDXMLOntologyPullParser', 'EDXMLOntologyPushParser',
           'EDXMLPullFilter', 'EDXMLPushFilter', 'ontology', 'transcode', 'Template', '__version__']
