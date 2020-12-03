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

from edxml import EventCollection
from edxml.error import EDXMLMergeConflictError
from edxml_test_corpus import CORPUS_PATH

corpus_path = CORPUS_PATH + '/conflict'


def test_parse_conflict():
    collection = EventCollection.from_edxml(open(corpus_path + '/conflict.edxml', 'rb').read())
    e = None
    try:
        collection.resolve_collisions()
    except EDXMLMergeConflictError as ex:
        e = ex

    # Parser must have raised a conflict error.
    assert e is not None


def test_parse_non_conflict():
    collection = EventCollection.from_edxml(open(corpus_path + '/no-conflict.edxml', 'rb').read())

    # Not a conflict, no exception raised.
    collection.resolve_collisions()
