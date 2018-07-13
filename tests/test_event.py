# coding=utf-8
# the line above is required for inline unicode
from edxml.event import EDXMLEvent


def test_event_init():
    content = u"Två dagar kvar🎉🎉"
    event = EDXMLEvent({}, event_type_name=None, source_uri=None, parents=None, content=content)

    assert event.get_content() == content
