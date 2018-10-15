from edxml.ontology import Ontology, EventSource
from edxml.EDXMLBase import EDXMLValidationError
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
    'test',
    'test/',
    'test/test/',
    '/test/test',
    '/test//',
    '//test/',
])
def fixedvaliduri(request):
    return request.param


@pytest.fixture(params=[
    '',
    '/',
    '//',
    '/test//test/',
])
def invaliduri(request):
    return request.param


def test_init_validuri(ontology, validuri):
    es = EventSource(ontology, validuri)
    assert es.get_uri() == validuri
    assert es.validate() == es


def test_init_fixedvaliduri(ontology, fixedvaliduri):
    # These URIs will be automatically fixed by the constructor to be valid
    es = EventSource(ontology, fixedvaliduri)
    assert es.get_uri().endswith('/')
    assert es.get_uri().startswith('/')
    assert es.validate() == es


def test_init_invaliduri(ontology, invaliduri):
    es = EventSource(ontology, invaliduri)
    with pytest.raises(EDXMLValidationError):
        es.validate()
