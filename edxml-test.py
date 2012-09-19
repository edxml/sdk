# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                       EDXML Specification Validator
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
#  Python script for checking EDXML data against the specification require-
#  ments. The script assumes that the data has already been validated against
#  the RelaxNG schema.

import sys
from xml.sax import make_parser
from edxml.EDXMLParser import EDXMLValidatingParser

class EDXMLChecker(EDXMLValidatingParser):
  
  def __init__ (self, upstream, SkipEvents = False):

    EDXMLValidatingParser.__init__(self, upstream, SkipEvents)
    
    self.ErrorCount = 0
    self.WarningCount = 0
  
  # Override of EDXMLParser implementation
  def Error(self, Message):
    if self.ErrorCount == 0:
      print ""
    
    print(unicode("ERROR: %s" % Message).encode('utf-8'))
    self.ErrorCount += 1
  
  # Override of EDXMLParser implementation
  def Warning(self, Message):
    if self.WarningCount == 0:
      print ""
      
    print(unicode("WARNING: " + Message).encode('utf-8'))
    self.WarningCount += 1

  def GetErrorCount(self):
    return self.ErrorCount
  
  def GetWarningCount(self):
    return self.WarningCount
    


SaxParser = make_parser()
MyChecker = EDXMLChecker(SaxParser)
SaxParser.setContentHandler(MyChecker)

if len(sys.argv) < 2:
  sys.stdout.write("\nNo filename was given, waiting for EDXML data on STDIN...")
  sys.stdout.flush()
  SaxParser.parse(sys.stdin)
else:
  sys.stdout.write("\nProcessing file %s:" % sys.argv[1] );
  SaxParser.parse(open(sys.argv[1]))

ErrorCount   = MyChecker.GetErrorCount()
WarningCount = MyChecker.GetWarningCount()

if ErrorCount == 0:
  sys.stdout.write("OK")
  sys.exit(0)
else:
  sys.stdout.write("\nInput data is invalid: %d errors were found ( and %d warnings ).\n" % (( ErrorCount, WarningCount )) )
  sys.exit(1)
  
