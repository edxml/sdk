from edxml.ontology import Ontology, EventSource
from edxml.error import EDXMLValidationError
import pytest


@pytest.fixture
def ontology():
    return Ontology()


@pytest.fixture(params=[
    '/a/',
    '/test/',
    '/test/test/'
])
def validuri(request):
    return request.param


@pytest.fixture(params=[
    '',
    '//',
    '/test',
    '/test//test/',
])
def invaliduri(request):
    return request.param


def test_init_validuri(ontology, validuri):
    es = EventSource(ontology, validuri)
    assert es.get_uri() == validuri
    assert es.validate() == es


def test_init_invaliduri(ontology, invaliduri):
    es = EventSource(ontology, invaliduri)
    with pytest.raises(EDXMLValidationError):
        es.validate()
