# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

"""
This package contains the EDXML SDK.
"""
from .version import __version__

from .template import Template
from .event import EDXMLEvent, EventElement, ParsedEvent
from .writer import EDXMLWriter
from .parser import EDXMLParserBase, EDXMLPullParser, EDXMLPushParser, EDXMLOntologyPullParser, EDXMLOntologyPushParser
from .filter import EDXMLFilterBase, EDXMLPullFilter, EDXMLPushFilter
from .event_collection import EventCollection

from . import ontology
from . import transcode


__all__ = ['EDXMLEvent', 'EventElement', 'ParsedEvent', 'EventCollection', 'EDXMLWriter',
           'EDXMLParserBase', 'EDXMLPullParser', 'EDXMLPushParser',
           'EDXMLOntologyPullParser', 'EDXMLOntologyPushParser',
           'EDXMLFilterBase', 'EDXMLPullFilter', 'EDXMLPushFilter', 'ontology', 'transcode', 'Template', '__version__']
