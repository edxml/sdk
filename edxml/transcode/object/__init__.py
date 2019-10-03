"""
This sub-package implements a transcoder to convert Python objects
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
from object_transcoder import ObjectTranscoder
from object_transcoder_mediator import ObjectTranscoderMediator


__all__ = ['ObjectTranscoder', 'ObjectTranscoderMediator']
