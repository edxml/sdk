import pytest
from edxml.transcode.object import ObjectTranscoderTestHarness, ObjectTranscoder


class TestObjectTranscoder(ObjectTranscoder):
    __test__ = False

    TYPES = ['system.user']
    TYPE_MAP = {'user': 'system.user'}
    TYPE_PROPERTIES = {'system.user': {'user.name': 'object-type.string'}}
    PROPERTY_MAP = {'system.user': {'name': 'user.name'}}

    def create_object_types(self):
        self._ontology.create_object_type('object-type.string')


@pytest.fixture()
def fixture_object():
    return {'type': 'user', 'name': 'Alice'}


def test(fixture_object):
    with ObjectTranscoderTestHarness(TestObjectTranscoder(), record_selector='type') as harness:
        harness.process_object(fixture_object)

    assert harness.events[0]['user.name'] == {'Alice'}
