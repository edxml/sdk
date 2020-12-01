import logging
import os

from edxml import EDXMLPullParser, EDXMLPushParser, EDXMLEvent, ParsedEvent


def test_basic_pull_parsing():
    with EDXMLPullParser() as parser:
        parser.parse(os.path.dirname(__file__) + '/input.edxml')
        assert parser.get_event_counter() == 2
        assert parser.get_event_type_counter('ea') == 1
        assert parser.get_event_type_counter('eb') == 1
        assert repr(parser.get_ontology()) == '2 event types, 1 object types, 2 sources and 0 concepts'


def test_basic_push_parsing():
    with EDXMLPushParser() as parser:
        parser.feed(open(os.path.dirname(__file__) + '/input.edxml', 'rb').read())
        assert parser.get_event_counter() == 2
        assert parser.get_event_type_counter('ea') == 1
        assert parser.get_event_type_counter('eb') == 1
        assert repr(parser.get_ontology()) == '2 event types, 1 object types, 2 sources and 0 concepts'


def test_event_type_handler(caplog):

    def handler(event):
        logging.info('handler called for ' + event.get_type_name())

    caplog.set_level(logging.INFO)

    with EDXMLPullParser() as parser:
        parser.set_event_type_handler(['ea'], handler)
        parser.parse(os.path.dirname(__file__) + '/input.edxml')

    assert caplog.messages == ['handler called for ea']

    caplog.clear()

    with EDXMLPullParser() as parser:
        parser.set_event_type_handler(['ea', 'eb'], handler)
        parser.parse(os.path.dirname(__file__) + '/input.edxml')

    assert 'handler called for ea' in caplog.messages
    assert 'handler called for eb' in caplog.messages


def test_event_source_handler(caplog):

    def handler(event: EDXMLEvent):
        logging.info('handler called for ' + event.get_source_uri())

    caplog.set_level(logging.INFO)

    with EDXMLPullParser() as parser:
        parser.set_event_source_handler(['/a/'], handler)
        parser.parse(os.path.dirname(__file__) + '/input.edxml')

    assert caplog.messages == ['handler called for /a/']

    caplog.clear()

    with EDXMLPullParser() as parser:
        parser.set_event_source_handler(['/(a|b)/'], handler)
        parser.parse(os.path.dirname(__file__) + '/input.edxml')

    assert 'handler called for /a/' in caplog.messages
    assert 'handler called for /b/' in caplog.messages


def test_custom_event_class():

    class CustomEvent(ParsedEvent):
        ...

    class TestParser(EDXMLPullParser):
        def _parsed_event(self, event):
            assert isinstance(event, CustomEvent)

    with TestParser() as parser:
        parser.set_custom_event_class(CustomEvent)
        parser.parse(os.path.dirname(__file__) + '/input.edxml')
