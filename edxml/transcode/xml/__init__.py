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

"""
This sub-package implements a transcoder to convert arbitrary XML
input streams into EDXML output streams. The various classes in this
package can be extended to implement transcoders for specific types of
XML elements and route XML element types to the correct transcoder.

..  autoclass:: XmlTranscoder
    :members:
    :show-inheritance:

..  autoclass:: XmlTranscoderMediator
    :members:
    :show-inheritance:
"""
from .xml_transcoder import XmlTranscoder
from .xml_transcoder_mediator import XmlTranscoderMediator
from .xml_test_harness import XmlTranscoderTestHarness

__all__ = ['XmlTranscoder', 'XmlTranscoderMediator', 'XmlTranscoderTestHarness']
