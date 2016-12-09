#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          EDXML Statistics Utility
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
#  This python script outputs various statistics for a set of EDXML files.
#  It prints event counts, lists defined event types, object types, source
#  URLs, and so on.

import string
import sys

from edxml.EDXMLParser import EDXMLPullParser


def PrintHelp():

  print """

   This utility outputs various statistics for a set of EDXML files. It
   prints event counts, lists defined event types, object types, source
   URLs, and so on.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. It can be specified multiple
                       times to get aggregated statistics for multiple
                       input files. If the argument is not used, input
                       data is read from standard input.

   Example:

     edxml-stats.py -f input01.edxml -f input02.edxml

"""

# Program starts here. 

ArgumentCount = len(sys.argv)
CurrentArgument = 1
InputFiles = []

# Parse commandline arguments

while CurrentArgument < ArgumentCount:

  if sys.argv[CurrentArgument] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrentArgument] == '-f':
    CurrentArgument += 1
    InputFiles.append((CurrentArgument, sys.argv[CurrentArgument]))

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrentArgument])
    sys.exit()

  CurrentArgument += 1

Parser = EDXMLPullParser(validate=False)

if len(InputFiles) == 0:

  # Feed the parser from standard input.
  InputFiles = [('standard input', sys.stdin)]
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

# We repeatedly use the same parser to process all EDXML files in succession.

for FileName, File in InputFiles:
  sys.stderr.write("Processing %s..." % FileName)

  try:
    Parser.parse(File)
  except KeyboardInterrupt:
    sys.exit(0)

print "\n"
print "Total event count: %s\n" % Parser.getEventCounter()
print "Event counts per type:\n"

for EventTypeName in sorted(Parser.getOntology().GetEventTypeNames()):
  print "%s: %s" % (string.ljust(EventTypeName, 40), Parser.getEventTypeCounter(EventTypeName))

print "\nObject Types:\n"

for ObjectTypeName in sorted(Parser.getOntology().GetObjectTypeNames()):
  DataType = Parser.getOntology().GetObjectType(ObjectTypeName).GetDataType()
  print "%s: %s" % (string.ljust(ObjectTypeName, 40), str(DataType))

predicates = set()
for EventTypeName, EventType in Parser.getOntology().GenerateEventTypes():
  for Relation in EventType.GetPropertyRelations():
    predicates.add(Relation.GetTypePredicate())

print "\nProperty relation predicates:\n"
for Predicate in sorted(predicates):
  print Predicate

print "\nSource URLs:\n"
for Url, Source in sorted(Parser.getOntology().GenerateEventSources()):
  print Url
