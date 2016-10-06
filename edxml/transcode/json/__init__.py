"""
This sub-package implements a transcoder to convert JSON records
into EDXML output streams. The various classes in this package
can be extended to implement transcoders for specific types of
JSON records and route JSON records to the correct transcoder.

..  autoclass:: JsonTranscoder
    :members:
    :show-inheritance:

..  autoclass:: JsonTranscoderMediator
    :members:
    :show-inheritance:
"""
from json_transcoder import JsonTranscoder
from json_transcoder_mediator import JsonTranscoderMediator
