#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                            EDXML Source Printer
#
#                  Copyright (c) 2010 - 2012 by D.H.J. Takken
#                          (d.h.j.takken@xs4all.nl)
#
#          This file is part of the EDXML Software Development Kit (SDK).
#
#
#  The EDXML SDK is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  The EDXML SDK is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with the EDXML SDK.  If not, see <http://www.gnu.org/licenses/>.
#
#
#  ===========================================================================
#
# 
#  Python script that outputs a list of source URLs that is found in 
#  specified EDXML file.

import sys
from xml.sax import make_parser
from xml.sax.saxutils import XMLGenerator, XMLFilterBase
from xml.sax.handler import ContentHandler
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLParser

class EDXMLParser(XMLFilterBase):

  def __init__ (self, upstream, SkipEvents = False):
  
    self.Sources = []
    self.SkipEvents = SkipEvents
    XMLFilterBase.__init__(self, upstream)
  
  def startElement(self, name, attrs):

    if name == 'source':
      Url = attrs.get('url',"")
      if not Url in self.Sources: self.Sources.append(Url)
  
  def endElement(self, name):

    if self.SkipEvents:
      if name == 'definitions':
  
        # We hit the end of the definitions block,
        # and we were instructed to skip parsing the
        # event data, so we should abort parsing now.
        raise EDXMLProcessingInterrupted('')


SaxParser = make_parser()

Parser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(Parser)
sys.stderr.write("Waiting for XML data on stdin...")

try:
  SaxParser.parse(open("/dev/stdin"))
except EDXMLProcessingInterrupted:
  pass

for Source in Parser.Sources:
  print Source
