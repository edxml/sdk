#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          Relative EDXML Validator
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
#  Python script that checks if the ontologies in de <definitions>
#  sections in all specified EDXML files are compatible.

import sys
from xml.sax import make_parser
from edxml.EDXMLParser import EDXMLParser
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted

def PrintHelp():

  print """

   This utility checks if the ontologies in de <definitions>
   sections in all specified EDXML files are compatible or not.
   Only compatible EDXML files can be merged. If all files prove
   compatible, the exit status is zero.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. It must be specified at
                       least twice.

   Example:

     edxml-check-compatibility.py -f input01.edxml -f input02.edxml

"""

# Program starts here. 

ArgumentCount = len(sys.argv)
CurrentArgument = 1
InputFileNames = []

# Parse commandline arguments

while CurrentArgument < ArgumentCount:

  if sys.argv[CurrentArgument] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrentArgument] == '-f':
    CurrentArgument += 1
    InputFileNames.append(sys.argv[CurrentArgument])

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrentArgument])
    sys.exit()

  CurrentArgument += 1

if len(InputFileNames) < 2:
  sys.stderr.write("Please specify at least two EDXML files. Use the --help argument to get help.\n")
  sys.exit()

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
Parser    = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(Parser)

# Now we feed each of the input files
# to the Sax parser. This will effectively
# cause the EDXMLParser instance to try and
# merge the <definitions> sections of all
# input files, raising EDXMLError when it
# detects a problem.

for FileName in InputFileNames:
  print("Checking %s" % FileName)
  
  try:
    SaxParser.parse(open(FileName))
  except EDXMLProcessingInterrupted:
    pass
  except EDXMLError as Error:
    print("EDXML file %s is incompatible with previous files:\n%s" % (( FileName, str(Error) )) )
  except:
    raise

if Parser.GetErrorCount() == 0:
  print("Files are compatible.")

# Print results.
print("\n\nTotal Warnings: %d\nTotal Errors:   %d\n\n" % (( Parser.GetWarningCount(), Parser.GetErrorCount() )) )    

if Parser.GetErrorCount() == 0:
  sys.exit(0)
else:
  sys.exit(255)