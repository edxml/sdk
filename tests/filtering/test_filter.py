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

import os

from io import BytesIO
from edxml import EDXMLPullFilter, EventCollection, EDXMLPushFilter


class PullFilter(EDXMLPullFilter):
    def __init__(self, output):
        super().__init__(output)
        self.input_events = []

    def _parsed_event(self, event):
        super()._parsed_event(event)
        self.input_events.append(event)


class PushFilter(EDXMLPushFilter):
    def __init__(self, output):
        super().__init__(output)
        self.input_events = []

    def _parsed_event(self, event):
        super()._parsed_event(event)
        self.input_events.append(event)


def test_parsed_event_callback_pull():
    with PullFilter(open(os.devnull, 'wb')) as edxml_filter:
        edxml_filter.parse(os.path.dirname(__file__) + '/input.edxml')
        assert len(edxml_filter.input_events) == 2


def test_parsed_event_callback_push():
    with PushFilter(open(os.devnull, 'wb')) as edxml_filter:
        edxml_filter.feed(open(os.path.dirname(__file__) + '/input.edxml', 'rb').read())
        assert len(edxml_filter.input_events) == 2


def test_pass_through():
    output = BytesIO()
    input_file = os.path.dirname(__file__) + '/input.edxml'

    with PullFilter(output) as edxml_filter:
        edxml_filter.parse(input_file)

    input_events = EventCollection.from_edxml(open(input_file, 'rb').read())
    output_events = EventCollection.from_edxml(output.getvalue())

    assert output_events.is_equivalent_of(input_events)


def test_delete_event():
    output = BytesIO()
    input_file = os.path.dirname(__file__) + '/input.edxml'

    class DeletingFilter(PullFilter):
        def _parsed_event(self, event):
            if 'delete me' not in event['pa']:
                # Event must not be deleted, so call
                # parent to pass it to the output.
                super()._parsed_event(event)

    with DeletingFilter(output) as edxml_filter:
        edxml_filter.parse(input_file)

    output_events = EventCollection.from_edxml(output.getvalue())

    # We should have just one event left.
    assert len(output_events) == 1


def test_edit_event():
    output = BytesIO()
    input_file = os.path.dirname(__file__) + '/input.edxml'

    class DeletingFilter(PullFilter):
        def _parsed_event(self, event):
            if 'delete me' in event['pa']:
                # Delete event property
                del event['pa']

            super()._parsed_event(event)

    with DeletingFilter(output) as edxml_filter:
        edxml_filter.parse(input_file)

    output_events = EventCollection.from_edxml(output.getvalue())

    # We should have no events containing 'delete me' anymore.
    assert [event for event in output_events if 'delete me' in event['pa']] == []
