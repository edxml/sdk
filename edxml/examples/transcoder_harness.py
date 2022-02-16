import pytest

from edxml.transcode.object import ObjectTranscoderTestHarness, ObjectTranscoder
from edxml_bricks.computing.generic import ComputingBrick


class TestObjectTranscoder(ObjectTranscoder):
    __test__ = False

    TYPES = ['com.acme.staff.account']
    TYPE_MAP = {'user': 'com.acme.staff.account'}
    PROPERTY_MAP = {
        'com.acme.staff.account': {
            'name': 'user.name'
        }
    }
    TYPE_PROPERTIES = {
        'com.acme.staff.account': {
            'user.name': ComputingBrick.OBJECT_USER_NAME
        }
    }


@pytest.fixture()
def fixture_object():
    return {'type': 'user', 'name': 'Alice'}


def test(fixture_object):
    with ObjectTranscoderTestHarness(TestObjectTranscoder(), record_selector='type') as harness:
        harness.process_object(fixture_object)

    assert harness.events[0]['user.name'] == {'Alice'}
