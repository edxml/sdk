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

# List of corpus directories corresponding to the EDXML
# versions that we support.
versions = ['3/3.0/3.0.0']

corpus_path = CORPUS_PATH + '/conflict'


def test_parse_conflict():
    for version_dir in versions:
        conflict_dir = CORPUS_PATH + version_dir + '/conflict'
        collection = EventCollection.from_edxml(open(conflict_dir + '/conflict.edxml', 'rb').read())
        e = None
        try:
            collection.resolve_collisions()
        except EDXMLMergeConflictError as ex:
            e = ex

        # Parser must have raised a conflict error.
        assert e is not None


def test_parse_non_conflict():
    for version_dir in versions:
        non_conflict_dir = CORPUS_PATH + version_dir + '/conflict'
        collection = EventCollection.from_edxml(open(non_conflict_dir + '/no-conflict.edxml', 'rb').read())

        # Not a conflict, no exception raised.
        collection.resolve_collisions()
