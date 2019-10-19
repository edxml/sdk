class EDXMLError(Exception):
    """Generic EDXML exception class"""
    pass


class EDXMLValidationError(EDXMLError):
    """Exception for signaling EDXML validation errors"""
    pass
