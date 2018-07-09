#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                          EDXML Merging Utility
#
#                            EXAMPLE APPLICATION
#
#                  Copyright (c) 2010 - 2016 by D.H.J. Takken
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
#  This utility reads multiple compatible EDXML files and merges them into
#  one new EDXML file, which is then printed on standard output. It works in
#  two passes. First, it compiles and integrates all <ontology> elements
#  from all EDXML files into a EDXMLParser instance. Then, in a second pass,
#  it outputs the unified <ontology> element and outputs the eventgroups
#  in each of the EDXML files.
#
#  The script demonstrates the use of EDXMLStreamFilter and merging of
#  <ontology> elements from multiple EDXML sources.

import sys
from xml.sax import make_parser
from xml.sax.xmlreader import AttributesImpl
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLParser
from edxml.EDXMLFilter import EDXMLStreamFilter

# This class is based on the EDXMLStreamFilter class,
# and filters out <eventgroup> sections, omitting
# all other content. It needs a dictionary which
# translates Source URLs to a new set of unique
# Source Identifiers. This mapping is used to translate
# the source-id attributes in the <eventgroup> tags,
# assuring the uniqueness of Source ID.


class EDXMLMerger(EDXMLStreamFilter):
    def __init__(self, upstream, MergedDefinitions, SourceUrlIdMapping):

        # Call parent constructor
        EDXMLStreamFilter.__init__(self, upstream, False)

        # Initialize source id / url mappings
        self.SourceUrlIdMapping = SourceUrlIdMapping
        self.SourceIdUrlMapping = {}

        self.Feedback = False
        self.DefinitionsWritten = False
        self.MergedDefinitions = MergedDefinitions

    def Close(self):
        self.SetOutputEnabled(True)
        EDXMLStreamFilter.endElement(self, 'eventgroups')
        EDXMLStreamFilter.endElement(self, 'events')

    def startElement(self, name, attrs):
        AttributeItems = {}
        # Populate the AttributeItems dictionary.
        for AttributeName, AttributeValue in attrs.items():
            AttributeItems[AttributeName] = AttributeValue

        if self.Feedback:
            # We are in the process of feeding ourselves
            # with merged definitions. Just pass through
            # whatever it is.
            EDXMLStreamFilter.startElement(
                self, name, AttributesImpl(AttributeItems))
            return

        if name == 'events':
            if self.DefinitionsWritten:
                # This is the <events> tag from a second, third, ...
                # EDXML stream that is fed to us. Turn output off
                # until we get to a <eventgroup> tag.
                self.SetOutputEnabled(False)
                return

        if name == 'definitions' and not self.Feedback:
            # Turn filter output off.
            self.SetOutputEnabled(False)
            return

        if name == 'source' and not self.Feedback:
            # Store the relations between source URL and ID
            self.SourceIdUrlMapping[AttributeItems['source-id']
                                    ] = AttributeItems['url']

        if name == 'eventgroup':

            # Edit the AttributeItems dictionary to ensure that the
            # source IDs in the output stream are unique.
            GroupSourceUrl = self.SourceIdUrlMapping[AttributeItems['source-id']]
            AttributeItems['source-id'] = self.SourceUrlIdMapping[GroupSourceUrl]

            # Turn output back on.
            self.SetOutputEnabled(True)

        if name == 'eventgroups' and self.DefinitionsWritten:
            self.SetOutputEnabled(True)
            return

        EDXMLStreamFilter.startElement(
            self, name, AttributesImpl(AttributeItems))

    def endElement(self, name):

        if name == 'definitions' and not self.DefinitionsWritten and not self.Feedback:
            self.Feedback = True
            self.SetOutputEnabled(True)
            self.MergedDefinitions.GenerateXMLDefinitions(self)
            self.Feedback = False

            # Output a <eventgroups> tag
            EDXMLStreamFilter.startElement(
                self, 'eventgroups', AttributesImpl({}))

            self.DefinitionsWritten = True

            # Turn filter output off.
            # self.SetOutputEnabled(False)
            return

        if name == 'eventgroups':
            self.SetOutputEnabled(False)
            return

        # Call parent implementation
        EDXMLStreamFilter.endElement(self, name)


def PrintHelp():

    print """

   This utility reads multiple compatible EDXML files and merges them into
   one new EDXML file, which is then printed on standard output.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input.

   Example:

     edxml-merge.py -f input1.edxml -f input2.edxml > output.edxml

"""

# Program starts here. Check commandline arguments.


CurrOption = 1
InputFileNames = []

while CurrOption < len(sys.argv):

    if sys.argv[CurrOption] in ('-h', '--help'):
        PrintHelp()
        sys.exit(0)

    elif sys.argv[CurrOption] == '-f':
        CurrOption += 1
        InputFileNames.append(sys.argv[CurrOption])

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[CurrOption])
        sys.exit()

    CurrOption += 1


if len(InputFileNames) < 2:
    sys.stderr.write("Please specify at least two EDXML files for merging.\n")
    sys.exit()

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
EDXMLParser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(EDXMLParser)

# First, we parse all specified EDXML files
# using the EDXMLParser, which will compile
# and merge all event type, object type
# and source definitions in the EDXML files.

for FileName in InputFileNames:
    sys.stderr.write("\nParsing file %s:" % FileName)

    try:
        SaxParser.parse(open(FileName))
    except EDXMLProcessingInterrupted:
        pass
    except EDXMLError as Error:
        sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (
            FileName, str(Error)))
        sys.exit(1)
    except Exception:
        raise

# Use the EDXMLDefinitions instance of EDXMLParser to
# generate a set of new, unique source IDs. The resulting
# dictionary maps Source URLs to source IDs.

SourceIdMapping = EDXMLParser.Definitions.UniqueSourceIDs()

SaxParser = make_parser()
Merger = EDXMLMerger(SaxParser, EDXMLParser.Definitions, SourceIdMapping)

SaxParser.setContentHandler(Merger)

# Now we process each of the specified EDXML files
# a second time. We will feed each file into the
# Merger, which will output the merged
# definitions and translate event source IDs.

for FileName in InputFileNames:
    sys.stderr.write("\nMerging file %s:" % FileName)

    try:
        SaxParser.parse(open(FileName))
    except EDXMLProcessingInterrupted:
        pass
    except EDXMLError as Error:
        sys.stderr.write("\n\nEDXML file %s is incompatible with previous files:\n\n%s" % (
            (FileName, str(Error))))
        sys.exit(1)
    except Exception:
        raise

# Finish the EDXML stream.
Merger.Close()
