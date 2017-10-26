#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                   EDXML to column separated text converter
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
#  This script accepts EDXML data as input and writes the events to standard
#  output, formatted in rows and columns. For every event property, a output
#  column is generated. If one property has multiple objects, multiple output
#  lines are generated.

import sys

from edxml.EDXMLParser import EDXMLPullParser


class EDXML2CSV(EDXMLPullParser):

  def __init__(self, OutputColumnNames, ColumnSeparator, PrintHeaderLine):

    self.PropertyNames = []
    self.ColumnSeparator = ColumnSeparator
    self.OutputColumnNames = OutputColumnNames
    self.PrintHeaderLine = PrintHeaderLine
    super(EDXML2CSV, self).__init__(sys.stdout)

  def _parsedOntology(self, ontology):

    # Compile a list of output columns,
    # one column per event property.
    PropertyNames = set()
    for EventTypeName, EventType in self.getOntology().GetEventTypes().iteritems():
        PropertyNames.update(EventType.GetProperties().keys())

    # Filter the available properties using
    # the list of requested output columns.
    if len(self.OutputColumnNames) > 0:
      for Property in self.OutputColumnNames:
        if Property in PropertyNames:
          self.PropertyNames.append(Property)
    else:
      # No output column specification was given,
      # just output all of them.
      self.PropertyNames = list(PropertyNames)

    # Output a header line containing the output column names
    if self.PrintHeaderLine:
      sys.stdout.write('event type' + self.ColumnSeparator + self.ColumnSeparator.join(self.PropertyNames) + '\n')

  def _parsedEvent(self, edxmlEvent):

    PropertyObjects = {}
    EscapedEventContent = edxmlEvent.GetContent().replace('\n', '\\n').replace(self.ColumnSeparator, '\\' + self.ColumnSeparator)

    for PropertyName in self.PropertyNames:
      PropertyObjects[PropertyName] = []

    for PropertyName, Objects in edxmlEvent.GetProperties().iteritems():
      if PropertyName in self.PropertyNames:
        for Object in Objects:
          EscapedValue = Object.replace(self.ColumnSeparator, '\\' + self.ColumnSeparator)
          PropertyObjects[PropertyName].append(EscapedValue)

        self.IterateGenerateLines(self.PropertyNames, PropertyObjects, edxmlEvent.GetTypeName() + self.ColumnSeparator,
                                  EscapedEventContent, 0)

  def IterateGenerateLines(self, Columns, PropertyObjects, LineStart, LineEnd, StartColumn):

    StartColPropertyName = Columns[StartColumn]

    if len(PropertyObjects[StartColPropertyName]) == 0:
      # Property has no objects, iterate.
      Line = LineStart + self.ColumnSeparator
      if len(Columns) > StartColumn + 1:
        self.IterateGenerateLines(Columns, PropertyObjects, Line, LineEnd, StartColumn + 1)
      return

    for ObjectValue in PropertyObjects[StartColPropertyName]:

      # Add object value to the current output line
      Line = LineStart + ObjectValue + self.ColumnSeparator

      for Column in range(StartColumn + 1, len(Columns)):

        ColumnProperty = Columns[Column]
        NumPropertyObjects = len(PropertyObjects[ColumnProperty])

        if NumPropertyObjects == 0:

          # Property has no objects.
          Line += self.ColumnSeparator

        elif NumPropertyObjects == 1:

          # We have exactly one object for this property.
          Line += PropertyObjects[ColumnProperty][0] + self.ColumnSeparator

        else:

          # We have multiple objects for this property,
          # which means we need to generate multiple output
          # lines. Iterate.
          self.IterateGenerateLines(Columns, PropertyObjects, Line, LineEnd, Column)
          return

      sys.stdout.write(unicode(Line + LineEnd + '\n').encode('utf-8'))


def PrintHelp():

  print """

   This utility accepts EDXML data as input and writes the events to standard
   output, formatted in rows and columns. For every event property, a output
   column is generated. If one property has multiple objects, multiple  output
   lines are generated.

   Options:

     -h, --help       Prints this help text

     -f               This option must be followed by a filename, which will be
                      used as input. If this option is not specified, EDXML data
                      will be read from standard input.

     -c, --columns    Specifies which columns to produce, and in what order. By
                      default, all columns are printed. When this option is used,
                      only the specified columns are printed, in the order you
                      specify. The argument should be a comma separated list of
                      property names.

     -s --separator   By default, columns are separated by tabs. Using this option,
                      you can specify a different separator.

     -s --noheader    By default, the first row is a header containing the names of
                      each column. Using this option, this header will be suppressed.

   Example:

     cat data.edxml | edxml-to-csv.py -c property-a,property-b -s ';'

"""

OutputColumns = []
Input = sys.stdin
ColumnSeparator = '\t'
SuppressHeaderLine = False
CurrOption = 1

while CurrOption < len(sys.argv):

  if sys.argv[CurrOption] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrOption] == '-f':
    CurrOption += 1
    Input = open(sys.argv[CurrOption])

  elif sys.argv[CurrOption] in ('-c', '--columns'):
    CurrOption += 1
    OutputColumns = sys.argv[CurrOption].split(',')

  elif sys.argv[CurrOption] in ('-s', '--separator'):
    CurrOption += 1
    ColumnSeparator = sys.argv[CurrOption]

  elif sys.argv[CurrOption] == '--noheader':
    CurrOption += 1
    SuppressHeaderLine = True

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrOption])
    sys.exit()

  CurrOption += 1

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
  EDXML2CSV(OutputColumns, ColumnSeparator, not SuppressHeaderLine).parse(Input)
except KeyboardInterrupt:
  sys.exit()
