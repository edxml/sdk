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
This sub-package implements a record transcoder to convert Python objects
into EDXML output streams. The various classes in this package
can be extended to implement transcoders for specific types of
Python objects and route them records to the correct transcoder.

..  autoclass:: ObjectTranscoder
    :members:
    :show-inheritance:

..  autoclass:: ObjectTranscoderMediator
    :members:
    :show-inheritance:
"""
from .object_transcoder import ObjectTranscoder
from .object_transcoder_mediator import ObjectTranscoderMediator
from .object_test_harness import ObjectTranscoderTestHarness


__all__ = ['ObjectTranscoder', 'ObjectTranscoderMediator', 'ObjectTranscoderTestHarness']
