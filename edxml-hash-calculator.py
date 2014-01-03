#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                        EDXML Sticky Hash Calculator
#
#                  Copyright (c) 2010 - 2014 by D.H.J. Takken
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
#  This script outputs sticky hashes for every event in a given 
#  EDXML file or input stream. The hashes are printed to standard output.

import sys
from xml.sax import make_parser
from edxml.EDXMLParser import EDXMLParser

# We create a class based on EDXMLParser,
# overriding the ProcessEvent to process
# the events in the EDXML stream.

class EDXMLEventHasher(EDXMLParser):
  
  def __init__ (self, upstream):

    EDXMLParser.__init__(self, upstream)
  
  # Override of EDXMLParser implementation
  def ProcessEvent(self, EventTypeName, SourceId, EventObjects, EventContent, ExplicitParents):

    # Use the EDXMLDefinitions instance in the 
    # EDXMLParser class to compute the sticky hash
    print self.Definitions.ComputeStickyHash(EventTypeName, EventObjects, EventContent)

# Create a SAX parser, and provide it with
# an EDXMLEventHasher instance as content handler.
# This places the EDXMLEventHasher instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
SaxParser.setContentHandler(EDXMLEventHasher(SaxParser))

# Now we feed EDXML data into the Sax parser. This will trigger
# calls to ProcessEvent in our EDXMLEventHasher, producing output.

if len(sys.argv) < 2:
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...")
  sys.stdout.flush()
  SaxParser.parse(sys.stdin)
else:
  sys.stderr.write("\nProcessing file %s:" % sys.argv[1] );
  SaxParser.parse(open(sys.argv[1]))
