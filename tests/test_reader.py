from edxml import EDXMLPullParser
import pytest


@pytest.fixture(
    scope="module",
    params=[
        {
            # ./edxml-ddgen.py --limit 5 > tests/testdata/random-5.edxml
            "filename": 'tests/testdata/random-5.edxml',
            "event_count": 5,
            "event_type_name": 'eventtype.a',
            "object_types": ['objecttype.c', 'objecttype.b', 'objecttype.a'],
        },
        {
            # ./edxml-ddgen.py --limit 10 > tests/testdata/random-10.edxml
            "filename": 'tests/testdata/random-10.edxml',
            "event_count": 10,
            "event_type_name": 'eventtype.a',
            "object_types": ['objecttype.c', 'objecttype.b', 'objecttype.a'],
        },
    ],
)
def data(request):
    request.param["file"] = open(request.param["filename"], 'rb')
    return request.param


def test_read(data):
    a = EDXMLPullParser()
    # Before parsing, event counter should be 0
    assert a.get_event_counter() == 0
    a.parse(data["file"])
    # After parsing, the event counter should be the number of events in the file
    assert a.get_event_counter() == data["event_count"]
    # The event counter for our specific event type should be the same
    assert a.get_event_type_counter(
        data["event_type_name"]) == data["event_count"]
    # Our object types should be parsed correctly and in order
    assert list(a.get_ontology().get_object_types().keys()) == data["object_types"]


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
