#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                      EDXML Ontology Replacement Utility
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
#  This utility replaces the eventtype definition of one EDXML file with those
#  contained in another EDXML file. The resulting EDXML stream is validated
#  against the new ontology and written to standard output.

import sys
from xml.sax import make_parser
from xml.sax.xmlreader import AttributesImpl
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLParser
from edxml.EDXMLFilter import EDXMLStreamFilter

class EDXMLDefinitionSwapper(EDXMLStreamFilter):
  """This class implements an EDXML filter which will
  replace eventtype definitions using the definitions in
  a EDXMLDefinitions instance."""

  def __init__ (self, upstream, Definitions, Output = sys.stdout):
    """ Constructor.

    You can pass any file-like object using the Output parameter, which
    will be used to send the filtered data stream to. It defaults to
    sys.stdout (standard output).

    Parameters:
    upstream    -- XML source (SaxParser instance in most cases)
    Definitions -- An EDXMLDefinitions instance containing the new definitions
    Output      -- An optional file-like object, defaults to sys.stdout
    """

    EDXMLStreamFilter.__init__(self, upstream, False, Output)

    self.NewDefinitions = Definitions
    self.Feedback = False

  def startElement(self, name, attrs):

    if self.Feedback:
      # We are feeding outselves with new
      # XML data. Just pass it through.
      EDXMLStreamFilter.startElement(self, name, attrs)
      return

    if name == 'eventtype':

      # Replace the attributes of the eventtype tag
      self.CurrentEventTypeName = attrs.get('name')
      if not self.CurrentEventTypeName in self.NewDefinitions.GetEventTypeNames():
        raise Exception("No new definition available for eventtype %s." % self.CurrentEventTypeName)
      attrs = AttributesImpl(self.NewDefinitions.GetEventTypeAttributes(self.CurrentEventTypeName))

      # Disable output. We will output the replacement
      # definition as soon as the closing tag has been read.
      self.SetOutputEnabled(False)
      return

    if name == 'objecttypes':

      # Disable output. We will output the replacement
      # definitions as soon as the closing tag has been read.
      EDXMLStreamFilter.startElement(self, 'objecttypes', AttributesImpl({}))
      self.SetOutputEnabled(False)

    EDXMLStreamFilter.startElement(self, name, attrs)

  def endElement(self, name):

    if self.Feedback:
      # We are feeding outselves with new
      # XML data. Just pass it through.
      EDXMLStreamFilter.endElement(self, name)
      return

    if name == 'eventtype':
      # Switch output back on.
      self.SetOutputEnabled(True)

      # Generate replacement eventtype definition, and feed the
      # resulting XML to ourselves. To prevent infinite feedback
      # loops, we keep track of the fact that we are currently
      # feeding back XML data to ourselves.
      self.Feedback = True
      self.NewDefinitions.GenerateEventTypeXML(self.CurrentEventTypeName, self)
      self.Feedback = False
      return

    if name == 'objecttypes':
      # Switch output back on.
      self.SetOutputEnabled(True)

      # Generate new objecttype definitions, and feed those
      # definitions to ourselves. To prevent infinite feedback
      # loops, we keep track of the fact that we are currently
      # feeding back XML data to ourselves.
      self.Feedback = True
      for ObjectTypeName in self.NewDefinitions.GetObjectTypeNames():
        self.NewDefinitions.GenerateObjectTypeXML(ObjectTypeName, self)
      self.Feedback = False

    EDXMLStreamFilter.endElement(self, name)

def PrintHelp():

  print """

   This utility replaces the eventtype definitions of one EDXML file with those
   contained in another EDXML file. The resulting EDXML stream is validated
   against the new ontology and written to standard output.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     cat input.edxml | edxml-replace-ontology.py -o ontology-source.edxml > output.edxml

"""

# Program starts here. 

ArgumentCount = len(sys.argv)
CurrentArgument = 1
OntologyFileName = None
Input = sys.stdin

# Parse commandline arguments

while CurrentArgument < ArgumentCount:

  if sys.argv[CurrentArgument] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrentArgument] == '-f':
    CurrentArgument += 1
    Input = open(sys.argv[CurrentArgument])

  elif sys.argv[CurrentArgument] == '-o':
    CurrentArgument += 1
    OntologyFileName = sys.argv[CurrentArgument]

  else:
    sys.stderr.write("\nUnknown commandline argument: %s" % sys.argv[CurrentArgument])
    sys.exit()

  CurrentArgument += 1

# Program starts here. Check commandline arguments.

if OntologyFileName == None:
  sys.stderr.write("No ontology source was specified. Use the --help option to get help.\n")
  sys.exit()

sys.stderr.write("\nUsing file '%s' as ontology source." % OntologyFileName );

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser   = make_parser()
EDXMLParser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(EDXMLParser)

# Parse the definitions from the specified
# EDXML file.

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
  SaxParser.parse(open(OntologyFileName))
except EDXMLProcessingInterrupted:
  pass
except EDXMLError as Error:
  sys.stderr.write("\n\nOntology source file '%s' is invalid EDXML:\n\n%s" % (( OntologyFileName, str(Error) )) )
  sys.exit(1)
except:
  raise


# Create a new SaxParser instance, and use that
# to instantiate EDXMLDefinitionSwapper. Pass the
# parsed definitions to the swapper.
SaxParser  = make_parser()
Swapper    = EDXMLDefinitionSwapper(SaxParser, EDXMLParser.Definitions)

SaxParser.setContentHandler(Swapper)

# Go!
SaxParser.parse(Input)
