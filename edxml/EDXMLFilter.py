# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                   Python classes for filtering EDXML data
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
#  ===========================================================================
#

"""EDXMLFilter

This module offers classes that combine EDXMLWriter and EDXMLParser to edit
EDXML data streams. By default, the input data is parsed and written into
the output. By overriding various callbacks, the data can be modified before
it is written, using an :class:`edxml.ontology.Ontology` instance to interpret it.

"""

from EDXMLParser import EDXMLParserBase, EDXMLPushParser, EDXMLPullParser
from edxml.EDXMLWriter import EDXMLWriter


class EDXMLFilter(EDXMLParserBase):
    """
    Extension of the push parser that copies its input
    to the specified output. By overriding the various
    callbacks provided by this class, the EDXML data can
    be manipulated before the data is output.
    """

    def __init__(self):
        super(EDXMLFilter, self).__init__()
        self._writer = None  # type: EDXMLWriter

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def _close(self):
        self._writer.close()

    def _parsed_ontology(self, parsed_ontology):
        """

        Callback that writes the parsed ontology into
        the output. By overriding this method and calling
        the parent method after changing the ontology, the
        ontology in the output stream can be modified.

        Args:
          parsed_ontology (edxml.ontology.Ontology): The ontology

        """
        super(EDXMLFilter, self)._parsed_ontology(parsed_ontology)
        self._writer.add_ontology(parsed_ontology)

    def _parsed_event(self, event):
        """

        Callback that writes the parsed event into
        the output. By overriding this method and calling
        the parent method after changing the event, the
        events in the output stream can be modified. If the
        parent method is not called, the event will be omitted
        in the output.

        Args:
          event (edxml.ParsedEvent): The event

        """
        super(EDXMLFilter, self)._parsed_event(event)
        self._writer.add_event(event)


class EDXMLPullFilter(EDXMLPullParser, EDXMLFilter):
    """
    Extension of the pull parser that copies its input
    to the specified output. By overriding the various
    callbacks provided by this class (or rather, the
    EDXMLFilter class), the EDXML data can be manipulated
    before the data is output.
    """

    def __init__(self, output, validate=True):
        super(EDXMLPullFilter, self).__init__()
        self._writer = EDXMLWriter(output, validate)

    def _parsed_event(self, event):
        EDXMLFilter._parsed_event(self, event)


class EDXMLPushFilter(EDXMLPushParser, EDXMLFilter):
    """
    Extension of the push parser that copies its input
    to the specified output. By overriding the various
    callbacks provided by this class (or rather, the
    EDXMLFilter class), the EDXML data can be manipulated
    before the data is output.
    """

    def __init__(self, output, validate=True):
        super(EDXMLPushFilter, self).__init__()
        self._writer = EDXMLWriter(output, validate)
