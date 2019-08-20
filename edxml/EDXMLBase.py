# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                     Several commonly used Python classes.
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

"""This module contains generic (base)classes used throughout the SDK."""
import sys


class EDXMLError(Exception):
    """Generic EDXML exception class"""
    pass


class EDXMLValidationError(EDXMLError):
    """Exception for signaling EDXML validation errors"""
    pass


class EDXMLBase(object):
    """Base class for most SDK subclasses"""

    def __init__(self):

        self.warning_count = 0
        self.error_count = 0

    def error(self, message):
        """Raises :class:`EDXMLError`.

        Args:
          message (str): Error message
        """

        self.error_count += 1
        raise EDXMLError(unicode("ERROR: " + message).encode('utf-8'))

    def warning(self, message):
        """Prints a warning to sys.stderr.

        Args:
          message (str): Warning message

        """
        self.warning_count += 1
        sys.stderr.write(unicode("WARNING: " + message + "\n").encode('utf-8'))

    def get_warning_count(self):
        """Returns the number of warnings generated"""
        return self.warning_count

    def get_error_count(self):
        """Returns the number of errors generated"""
        return self.error_count


class EvilCharacterFilter(object):
    """
    This class exports a single property named evil_xml_chars_regexp.
    It contains a compiled regular expression that matches all unicode
    characters that are illegal in XML, like control characters.

    Since the lxml library which this SDK is based on does not accept
    any of these characters as input, any code that uses lxml to
    generate XML must handle the TypeError exceptions that are thrown
    by lxml when attempting to feed it illegal characters.

    The regular expression produced by this class eases handling these
    exceptions.
    """

    def __init__(self):
        # The lxml package does not filter out illegal XML
        # characters. So, below we compile a regular expression
        # matching all ranges of illegal characters. We will
        # use that to do our own filtering.

        ranges = [
            (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
            (0x7F, 0x84), (0x86, 0x9F),
            (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)
        ]

        if sys.maxunicode >= 0x10000:  # not narrow build
            ranges.extend([
                (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)
            ])

        regexp_ranges = ["%s-%s" % (unichr(low), unichr(high))
                         for (low, high) in ranges]

        self.evil_xml_chars_regexp = u'[%s]' % u''.join(regexp_ranges)
