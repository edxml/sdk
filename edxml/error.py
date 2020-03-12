from lxml import etree


class EDXMLError(Exception):
    """Generic EDXML exception class"""
    pass


class EDXMLValidationError(EDXMLError):
    """Exception for signaling EDXML validation errors"""
    pass


class EDXMLMergeConflictError(EDXMLError):
    """Exception for signalling EDXML merge conflicts"""
    def __init__(self, events):
        """
        Create a merge conflict error from a set of conflicting
        events.

        Args:
            events (List[edxml.EDXMLEvent]): Conflicting events
        """
        super(EDXMLMergeConflictError, self).__init__(
            'A merge conflict was detected between the following events:' + '\n'.join(
                [etree.tostring(e, pretty_print=True, encoding='unicode') for e in events]
            )
        )
