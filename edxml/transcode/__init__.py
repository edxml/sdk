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
This sub-package contains several classes to ease development of record transcoders that convert
various types of input data (like JSON records) into EDXML output streams.

..  autoclass:: RecordTranscoder
    :members:
    :show-inheritance:

..  autoclass:: TranscoderMediator
    :members:
    :show-inheritance:
"""
from .transcoder import RecordTranscoder
from .mediator import TranscoderMediator
from .test_harness import TranscoderTestHarness


__all__ = ['RecordTranscoder', 'TranscoderMediator', 'TranscoderTestHarness']
