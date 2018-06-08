# coding=utf-8
# the line above is required for inline unicode
from edxml.event import EDXMLEvent

def test_event_init():
    content = u"Två dagar kvar🎉🎉"
    event = EDXMLEvent([], EventTypeName = None, SourceUri = None, Parents = None, Content=content)

    assert event.Content == content