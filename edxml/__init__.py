"""
This package contains the EDXML SDK.
"""
import sys

from .version import __version__

from .event import EDXMLEvent, EventElement, ParsedEvent
from .event_collection import EventCollection
from .EDXMLWriter import EDXMLWriter
from .SimpleEDXMLWriter import SimpleEDXMLWriter
from .EDXMLParser import EDXMLPullParser, EDXMLPushParser, EDXMLOntologyPullParser, EDXMLOntologyPushParser
from .EDXMLFilter import EDXMLPullFilter, EDXMLPushFilter

from . import ontology
from . import transcode

namespace = {None: 'http://edxml.org/edxml'}

# The lxml package does not filter out illegal XML
# characters. So, below we compile a regular expression
# matching all ranges of illegal characters. We will
# use that to do our own filtering.

ranges = [
    (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
    (0x7F, 0x84), (0x86, 0x9F),
    (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)
]

if sys.maxunicode >= 0x10000:  # not narrow build
    ranges.extend([
        (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
        (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
        (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
        (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
        (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
        (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
        (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
        (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)
    ])


evil_xml_chars_regexp = '[%s]' % ''.join(
    ["%s-%s" % (chr(low), chr(high)) for (low, high) in ranges]
)

__all__ = ['EDXMLEvent', 'EventElement', 'ParsedEvent', 'EventCollection', 'EDXMLWriter', 'SimpleEDXMLWriter',
           'EDXMLPullParser', 'EDXMLPushParser', 'EDXMLOntologyPullParser', 'EDXMLOntologyPushParser',
           'EDXMLPullFilter', 'EDXMLPushFilter', 'ontology', 'transcode', '__version__']
