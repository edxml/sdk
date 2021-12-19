# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

"""filter

This module offers classes that combine EDXMLWriter and EDXMLParser to edit
EDXML data streams. By default, the input data is parsed and written into
the output. By overriding various callbacks, the data can be modified before
it is written, using an :class:`edxml.ontology.Ontology` instance to interpret it.

"""
from .parser import EDXMLParserBase, EDXMLPushParser, EDXMLPullParser
from edxml.writer import EDXMLWriter


class EDXMLFilterBase(EDXMLParserBase):
    """
    Extension of the EDXML parser that copies its input
    to the specified output. This class should not be
    instantiated. Instead, use one either EDXMLPullFilter
    or EDXMLPushFilter.
    """

    def __init__(self, output, validate=True):
        super().__init__(validate)
        self._writer = self._writer = EDXMLWriter(output, validate)  # type: EDXMLWriter
        """EDXML Writer"""

    def _close(self):
        self._writer.close()

    def _parsed_ontology(self, parsed_ontology, filtered_ontology=None):
        """

        Callback that writes the parsed ontology into
        the output. By overriding this method and calling
        the parent method while passing a modified copy of
        the parsed ontology the output stream can be modified.

        Args:
          parsed_ontology (edxml.ontology.Ontology): The input ontology
          filtered_ontology (edxml.ontology.Ontology): The output ontology

        """
        super()._parsed_ontology(parsed_ontology)
        self._writer.add_ontology(filtered_ontology or parsed_ontology)

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
        super()._parsed_event(event)
        self._writer.add_event(event)


class EDXMLPullFilter(EDXMLPullParser, EDXMLFilterBase):
    """
    Extension of the pull parser that copies its input
    to the specified output. By overriding the various
    callbacks provided by this class (or rather, the
    EDXMLFilterBase class), the EDXML data can be manipulated
    before the data is output.
    """

    def __init__(self, output, validate=True):
        EDXMLPullParser.__init__(self, validate)
        EDXMLFilterBase.__init__(self, output, validate)


class EDXMLPushFilter(EDXMLPushParser, EDXMLFilterBase):
    """
    Extension of the push parser that copies its input
    to the specified output. By overriding the various
    callbacks provided by this class (or rather, the
    EDXMLFilterBase class), the EDXML data can be manipulated
    before the data is output.
    """

    def __init__(self, output, validate=True):
        EDXMLPushParser.__init__(self, validate)
        EDXMLFilterBase.__init__(self, output, validate)
