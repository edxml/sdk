#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                            Event data stripper
#
#                            EXAMPLE APPLICATION
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
# 
#  Python script that will filter out the event data from EDXML and validate the
#  ontology in the <definitions> section in the process. The stripped version of
#  the input.

import sys
from xml.sax import make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl
from edxml.EDXMLParser import EDXMLParser
from edxml.EDXMLBase import EDXMLProcessingInterrupted

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
Parser    = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(Parser)

# Read commandline parameters

if len(sys.argv) >= 2:
  sys.stderr.write("\nProcessing %s" % sys.argv[1])
  Input = open(sys.argv[1])
else:
  Input = sys.stdin
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...")
  sys.stdout.flush()

# Feed the input to the Sax parser. This
# will parse the <definitions> section and
# raise EDXMLProcessingInterrupted when done.

try:
  SaxParser.parse(Input)
except EDXMLProcessingInterrupted:
  pass
except:
  raise

# Instantiate an XMLGenerator and generate opening
# <events> tag.
Generator = XMLGenerator(sys.stdout, 'utf-8')
Generator.startElement('events', AttributesImpl({}))

# Use the EDXMLDefinitions instance of the parser to
# generate a <definitions> section.
Parser.Definitions.GenerateXMLDefinitions(Generator, False)

# Generate some more XML tags to complete the output, generating
# valid stripped EDXML output.
Generator.startElement('eventgroups', AttributesImpl({}))
Generator.endElement('eventgroups')
Generator.endElement('events')
