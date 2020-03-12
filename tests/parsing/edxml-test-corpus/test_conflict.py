import os

from edxml import EventCollection
from edxml.error import EDXMLMergeConflictError

corpus_path = os.path.dirname(os.path.abspath(__file__)) + '/corpus/conflict'


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
