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

import sys
import time
import edxml


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

     -u --source-uri  This option must be followed by the EDXML source URI that represents
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
OutputSourceUri = None
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

  elif sys.argv[CurrOption] in ('-u', '--source-uri'):
    CurrOption += 1
    OutputSourceUri = sys.argv[CurrOption]

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

if OutputSourceUri is None:
  sys.stderr.write('No source URI was specified. (use --help option to get help)\n')
  sys.exit(1)

if EventTypeColumn is None and OutputEventType is None:
  sys.stderr.write('I cannot determine the event type of the input data. Either specify an event type or a column that contains event type names. (use --help option to get help)\n')
  sys.exit(1)

Parser = edxml.EDXMLOntologyPullParser()

try:
  Parser.parse(OntologyInputFile)
except edxml.EDXMLOntologyPullParser.ProcessingInterrupted:
  pass

# Remove the existing source definitions, we will
# define our own data source.
for uri, source in Parser.getOntology().GetEventSources():
  Parser.getOntology().DeleteEventSource(uri)

# Define new data source.
Parser.getOntology().CreateEventSource(
  OutputSourceUri, Description='Imported from CSV data', AcquisitionDate=DateAcquired
)

if Input == sys.stdin:
  sys.stderr.write('Waiting for CSV data on standard input... (use --help option to get help)\n')

# Instantiate an EDXMLWriter and insert the <definitions> element
# from the input EDXML file. This duplicates the <definitions>
# element from the input EDXML file, except for the source
# definitions that we replaced with our own.
MyWriter = edxml.EDXMLWriter(sys.stdout)
MyWriter.AddOntology(Parser.getOntology())

# We will start outputting event groups now.
MyWriter.OpenEventGroups()

CurrentOutputEventType = None
ColumnPropertyMapping = None
PreviousSplitLine = None
PreviousLineProperties = None
OutputEvent = edxml.EventElement({}, OutputEventType, OutputSourceUri)
OutputProperties = {}
UniqueOutputProperties = {}

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

  if OutputEventType not in OutputProperties:
    OutputProperties[OutputEventType] = Parser.getOntology().GetEventType(OutputEventType).GetProperties()
    UniqueOutputProperties[OutputEventType] = Parser.getOntology().GetEventType(OutputEventType).GetUniqueProperties()

    OutputProperties[OutputEventType] = [Property for Property in OutputProperties[OutputEventType] if Property in PropertyColumnMapping]
    UniqueOutputProperties[OutputEventType] = [Property for Property in UniqueOutputProperties[OutputEventType] if Property in PropertyColumnMapping]

  # Create dictionary of properties and their objects
  LineProperties = {}
  for Property in OutputProperties[OutputEventType]:
    if SplitLine[PropertyColumnMapping[Property]] != '':
      LineProperties[Property] = [SplitLine[PropertyColumnMapping[Property]]]

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
      if len(DiffProperties) > 0 and DiffProperties[0] not in UniqueOutputProperties[OutputEventType]:
        Property = DiffProperties[0]

        # Add the value to existing dictionary and move on to the next line.
        PreviousLineProperties[Property].extend(LineProperties[Property])
        continue

    if OutputEventType != CurrentOutputEventType:
      if CurrentOutputEventType is not None:
        if PreviousLineProperties is not None:
          try:
            MyWriter.AddEvent(OutputEvent.SetProperties(PreviousLineProperties))
          except edxml.EDXMLValidationError as Error:
            # Invalid event, just skip it.
            sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)
        MyWriter.CloseEventGroup()
        MyWriter.OpenEventGroup(OutputEventType, OutputSourceUri)
      else:
        MyWriter.OpenEventGroup(OutputEventType, OutputSourceUri)
        if PreviousLineProperties is not None:
          try:
            MyWriter.AddEvent(OutputEvent.SetProperties(PreviousLineProperties))
          except edxml.EDXMLValidationError as Error:
            # Invalid event, just skip it.
            sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)
      CurrentOutputEventType = OutputEventType
    else:
      try:
        MyWriter.AddEvent(OutputEvent.SetProperties(PreviousLineProperties))
      except edxml.EDXMLValidationError as Error:
        # Invalid event, just skip it.
        sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)

  PreviousSplitLine = SplitLine
  PreviousLineProperties = LineProperties

if PreviousSplitLine is not None:
  if OutputEventType != CurrentOutputEventType:
    if CurrentOutputEventType is not None:
      MyWriter.CloseEventGroup()
    MyWriter.OpenEventGroup(OutputEventType, OutputSourceUri)
    CurrentOutputEventType = OutputEventType
    if OutputEventType not in OutputProperties:
      OutputProperties[OutputEventType] = Parser.getOntology().GetEventType(OutputEventType).GetProperties()
      UniqueOutputProperties[OutputEventType] = Parser.getOntology().GetEventType(OutputEventType).GetUniqueProperties()

      OutputProperties[OutputEventType] = [Property for Property in OutputProperties if Property in PropertyColumnMapping]
      UniqueOutputProperties[OutputEventType] = [Property for Property in UniqueOutputProperties if Property in PropertyColumnMapping]

    OutputEvent.SetType(OutputEventType)
  try:
    MyWriter.AddEvent(OutputEvent.SetProperties(PreviousLineProperties))
  except edxml.EDXMLValidationError as Error:
    # Invalid event, just skip it.
    sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)

if CurrentOutputEventType is not None:
  MyWriter.CloseEventGroup()

MyWriter.Close()
