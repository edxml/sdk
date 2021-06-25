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

from lxml import etree


class EDXMLError(Exception):
    """Generic EDXML exception class"""
    pass


class EDXMLValidationError(EDXMLError):
    """Exception for signaling EDXML validation errors"""
    pass


class EDXMLOntologyValidationError(EDXMLValidationError):
    """Exception for signaling EDXML ontology validation errors"""
    pass


class EDXMLEventValidationError(EDXMLValidationError):
    """Exception for signaling EDXML event validation errors"""
    pass


class EDXMLMergeConflictError(EDXMLValidationError):
    """Exception for signalling EDXML merge conflicts"""
    def __init__(self, events):
        """
        Create a merge conflict error from a set of conflicting
        events.

        Args:
            events (List[edxml.EDXMLEvent]): Conflicting events
        """
        super().__init__(
            'A merge conflict was detected between the following events:' + '\n'.join(
                [etree.tostring(e, pretty_print=True, encoding='unicode') for e in events]
            )
        )
