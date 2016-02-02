#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                  column separated text to EDXML converter
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
#  This script accepts column separated text as input and writes a EDXML data
#  stream to standard output. It uses the ontology from an existing EDXML file
#  to generate output. The input should have column names on the very first row,
#  where the column names match the names of the event type properties.

import sys, time
from StringIO import StringIO
from xml.sax import make_parser
from xml.sax.saxutils import XMLGenerator
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLValidatingParser
from edxml.EDXMLWriter import EDXMLWriter

def PrintHelp():

  print """

   This utility accepts column separated text as input and wraps the input data
   into an EDXML output stream, which is printed on standard output. The input
   data must contain a header line, which contains the names of the event properties
   that each column represents. An existing EDXML file is used to extract the event
   type definition from. Optionally, a column can be specified which contains the
   name of the event type that each input line represents. This allows multiple event
   types to be generated from a single CSV input stream.

   Options:

     -h, --help       Prints this help text

     -f               This option must be followed by a filename, which will be used to
                      read CSV input data from. If this option is not specified, data
                      will be read from standard input.

     -o               This option must be followed by a filename, which must contain
                      an EDXML stream which holds the ontology, containing the eventtype
                      definition that matches the CVS input data.

     -u --source-url  This option must be followed by the EDXML source URL that represents
                      the origin of the input data.

     -e --event-type  This option must be followed by the name of the event type that the
                      CSV data represents.

     -t --type-column This option must be followed by a column number of the column that
                      contains the name of the event type represented by each input line.
                      By default, unless -t is used, it is assumed that column #0 contains
                      the event type.

     -s --separator   By default, columns are assumed to be separated by tabs. Using this
                      option, you can specify a different separator.

   Example:

     cat data.csv | edxml-from-csv.py -o ontology.edxml -t my-eventtype -s ';'

"""

Input = sys.stdin
OntologyInputFile = None
ColumnSeparator = '\t'
OutputEventType = None
EventTypeColumn = None
OutputSourceUrl = None
CurrOption = 1
TimeAcquired = time.gmtime()
DateAcquired = "%04d%02d%02d" % (( TimeAcquired.tm_year, TimeAcquired.tm_mon, TimeAcquired.tm_mday ))

while CurrOption < len(sys.argv):

  if sys.argv[CurrOption] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrOption] == '-f':
    CurrOption += 1
    Input = open(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '-o':
    CurrOption += 1
    OntologyInputFile = open(sys.argv[CurrOption])

  elif sys.argv[CurrOption] in ('-u', '--source-url'):
    CurrOption += 1
    OutputSourceUrl = sys.argv[CurrOption]

  elif sys.argv[CurrOption] in ('-e', '--event-type'):
    CurrOption += 1
    OutputEventType = sys.argv[CurrOption]

  elif sys.argv[CurrOption] in ('-t', '--type-column'):
    CurrOption += 1
    EventTypeColumn = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] in ('-s', '--separator'):
    CurrOption += 1
    ColumnSeparator = sys.argv[CurrOption]

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrOption])
    sys.exit()

  CurrOption += 1

if OntologyInputFile is None:
  sys.stderr.write('No ontology source was specified. (use --help option to get help)\n')
  sys.exit(1)

if OutputSourceUrl is None:
  sys.stderr.write('No source URL was specified. (use --help option to get help)\n')
  sys.exit(1)

if EventTypeColumn is None and OutputEventType is None:
  sys.stderr.write('I cannot determine the event type of the input data. Either specify an event type or a column that contains event type names. (use --help option to get help)\n')
  sys.exit(1)

# Create a SAX parser, provide it with
# an EDXMLValidatingParser instance as content handler.
SaxParser = make_parser()
MyEDXMLParser = EDXMLValidatingParser(SaxParser, SkipEvents = True)
SaxParser.setContentHandler(MyEDXMLParser)

# Parse the EDXML file. This yields a parsed ontology
# in the EDXMLValidatingParser instance.
try:
  SaxParser.parse(OntologyInputFile)
except EDXMLProcessingInterrupted:
  pass

# Remove the existing source definitions, we will
# define our own data source.
for SourceId in MyEDXMLParser.Definitions.GetSourceIDs():
  MyEDXMLParser.Definitions.RemoveSource(SourceId)

# Define new data source.
MyEDXMLParser.Definitions.AddSource(OutputSourceUrl, {'source-id': 'csv', 'url': OutputSourceUrl, 'date-acquired' : DateAcquired, 'description': 'Imported from CSV data'})

# Generate the <definitions> element from the EDXML file we
# just parsed using MyEDXMLParser.
DefinitionsElement = StringIO()
MyEDXMLParser.Definitions.GenerateXMLDefinitions(XMLGenerator(DefinitionsElement, 'utf-8'))

if Input == sys.stdin:
  sys.stderr.write('Waiting for CSV data on standard input... (use --help option to get help)\n')

# Instantiate an EDXMLWriter and insert the <definitions> element
# from the input EDXML file. This duplicates the <definitions>
# element from the input EDXML file, except for the source
# definitions that we replaced with our own.
MyWriter = EDXMLWriter(sys.stdout, Validate = True, ValidateObjects = True)
MyWriter.AddXmlDefinitionsElement(DefinitionsElement.getvalue())

# We will start outputting event groups now.
MyWriter.OpenEventGroups()

CurrentOutputEventType = None
ColumnPropertyMapping = None
PreviousSplitLine = None
PreviousLineProperties = None

for Line in Input:
  if ColumnPropertyMapping is None:
    # Read header line.
    ColumnPropertyMapping = Line.rstrip('\n').split(ColumnSeparator)

    if EventTypeColumn is not None:
      # We have a column containing the event type name.
      del ColumnPropertyMapping[EventTypeColumn]

    # Build a dictionary containing a mapping from
    # property names to column indexes.
    PropertyColumnMapping = {Property: Index for Index, Property in dict(enumerate(ColumnPropertyMapping)).items()}

    # Since this is a header line, we stop
    # processing at this point.
    continue

  SplitLine = Line.rstrip('\n').split(ColumnSeparator)

  if EventTypeColumn is not None:
    # We have a column containing the event type name.
    OutputEventType = SplitLine[EventTypeColumn]
    del SplitLine[EventTypeColumn]

  # Create dictionary of properties and their objects
  LineProperties = {Property: [SplitLine[PropertyColumnMapping[Property]]] for Property in MyEDXMLParser.Definitions.GetEventTypeProperties(OutputEventType) if SplitLine[PropertyColumnMapping[Property]] != '' }

  if PreviousSplitLine is not None:

    # Compare with previous line, maybe
    # the lines form a single event having
    # multiple objects for the same property,
    # scattered over multiple consecutive lines.
    Difference = set(SplitLine) ^ set(PreviousSplitLine)

    if len(Difference) == 2:
      # This line is suspicious. Figure out which property
      # is different.
      DiffProperties = [Property for Property in LineProperties if LineProperties[Property] != PreviousLineProperties[Property]]

      # Check if we have exactly one differing property, which
      # must NOT be a unique property. Differing unique properties
      # always mean that we are looking at two different events.
      if len(DiffProperties) > 0 and DiffProperties[0] not in MyEDXMLParser.Definitions.GetUniqueProperties(OutputEventType):
        Property = DiffProperties[0]

        # Add the value to existing dictionary and move on to the next line.
        PreviousLineProperties[Property].extend(LineProperties[Property])
        continue

    if OutputEventType != CurrentOutputEventType:
      if CurrentOutputEventType is not None:
        if PreviousLineProperties is not None:
          try:
            MyWriter.AddEvent(PreviousLineProperties)
          except EDXMLError as Error:
            # Invalid event, just skip it.
            sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)
        MyWriter.CloseEventGroup()
        MyWriter.OpenEventGroup(OutputEventType, 'csv')
      else:
        MyWriter.OpenEventGroup(OutputEventType, 'csv')
        if PreviousLineProperties is not None:
          try:
            MyWriter.AddEvent(PreviousLineProperties)
          except EDXMLError as Error:
            # Invalid event, just skip it.
            sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)
      CurrentOutputEventType = OutputEventType
    else:
      try:
        MyWriter.AddEvent(PreviousLineProperties)
      except EDXMLError as Error:
        # Invalid event, just skip it.
        sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)

  PreviousSplitLine = SplitLine
  PreviousLineProperties = LineProperties

if PreviousSplitLine is not None:
  if OutputEventType != CurrentOutputEventType:
    if CurrentOutputEventType is not None:
      MyWriter.CloseEventGroup()
    MyWriter.OpenEventGroup(OutputEventType, 'csv')
    CurrentOutputEventType = OutputEventType
  try:
    MyWriter.AddEvent(PreviousLineProperties)
  except EDXMLError as Error:
    # Invalid event, just skip it.
    sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)

if CurrentOutputEventType is not None:
  MyWriter.CloseEventGroup()

MyWriter.CloseEventGroups()
