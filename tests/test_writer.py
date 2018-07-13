import pytest
from edxml import EDXMLPullParser, SimpleEDXMLWriter
from edxml.SocketEDXMLWriter import SocketEDXMLWriter
import socket
import threading
import time

from StringIO import StringIO


@pytest.fixture(
    params=[
        {
            # ./edxml-ddgen.py --limit 5 > tests/testdata/random-5.edxml
            "filename": 'tests/testdata/random-5.edxml',
            "event_types": ['eventtype.a']
        },
        {
            # ./edxml-ddgen.py --limit 10 > tests/testdata/random-10.edxml
            "filename": 'tests/testdata/random-10.edxml',
            "event_types": ['eventtype.a']
        },
    ],
)
def file(request):
    events = []

    def handler(edxml_event):
        events.append(edxml_event)

    a = EDXMLPullParser()
    a.set_event_type_handler(request.param["event_types"], handler=handler)
    a.parse(open(request.param["filename"]))
    request.param["parser"] = a
    request.param["events"] = events
    return request.param


class SocketBuffer:
    def __init__(self):
        self.buffer = ""

    def listen_and_return(self, listen):
        conn, address = listen.accept()
        while True:
            data = conn.recv(1024)
            if data:
                self.buffer += data
            else:
                break
        conn.close()


@pytest.fixture
def listener():
    # TODO: is listening on a random socket ok for a unit test that should be deterministic?
    address = ('localhost', 0)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # we tried setting nodelay but it didnt solve any buffering issues,
    # so let's not use it until we need it
    # s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.bind(address)
    s.listen(1)
    buffer = SocketBuffer()
    threading.Thread(target=buffer.listen_and_return, args=[s]).start()

    yield {
        "socket": s,
        "result_buffer": buffer,
    }
    s.close()


@pytest.fixture
def simplewriter(tmpdir):
    f = tmpdir.mkdir("sub").join("simplewriter.edxml")
    f.ensure(file=True)

    # f = open('tests/testdata/output.test', 'a+')
    f = f.open('a+')

    def validate():
        f.seek(0)
        p = EDXMLPullParser()
        p.parse(f)
        return p

    yield {
        "writer": SimpleEDXMLWriter(f),
        "validator": validate
    }

    # f.remove()


@pytest.fixture
def socketwriter(listener):
    def validate():
        stringfile = StringIO(listener["result_buffer"].buffer)
        p = EDXMLPullParser()
        p.parse(stringfile)
        listener["result_buffer"].buffer = ""
        return p

    return {
        "writer": SocketEDXMLWriter(listener["socket"].getsockname()),
        "validator": validate
    }


@pytest.fixture(
    params=[
        "simplewriter",
        "socketwriter",
    ]
)
def writer(request):
    return request.getfixturevalue(request.param)


def test_write(file, writer):
    edxml = writer["writer"]  # type: SimpleEDXMLWriter
    validator = writer["validator"]
    parser = file["parser"]  # type: EDXMLPullParser
    ontology = parser.get_ontology()
    edxml.add_ontology(ontology)
    edxml.set_buffer_size(0)
    for event in file["events"]:
        edxml.add_event(event)
    edxml.flush()
    edxml.close()

    time.sleep(1)
    validator_parser = validator()  # type: EDXMLPullParser
    assert parser.get_event_counter() == validator_parser.get_event_counter()


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
