import os
from glob import glob

import pytest

from edxml import EDXMLPullParser
from edxml.error import EDXMLValidationError

corpus_path = os.path.dirname(os.path.abspath(__file__)) + '/corpus/invalid'

# This glob pattern can be used to select a subset of
# files that will be tested, which may be useful when
# trouble shooting failing tests
file_glob = '*.edxml'


def generate_invalid_structure_fixture_params():
    path = corpus_path + '/structure'
    params = []
    for filename in os.listdir(path):
        if path + '/' + filename in glob(path + '/' + file_glob):
            params.append({'path': path + '/' + filename})
    return params


def generate_invalid_ontology_fixture_params():
    path = corpus_path + '/ontology'
    params = []
    for filename in os.listdir(path):
        if path + '/' + filename in glob(path + '/' + file_glob):
            params.append({'path': path + '/' + filename})
    return params


def generate_invalid_event_fixture_params():
    path = corpus_path + '/event'
    params = []
    for filename in os.listdir(path):
        if path + '/' + filename in glob(path + '/' + file_glob):
            params.append({'path': path + '/' + filename})
    return params


@pytest.fixture(scope='module', params=generate_invalid_structure_fixture_params())
def invalid_structure_corpus_item(request):
    request.param['file'] = open(request.param['path'])
    return request.param


@pytest.fixture(scope='module', params=generate_invalid_ontology_fixture_params())
def invalid_ontology_corpus_item(request):
    request.param['file'] = open(request.param['path'])
    return request.param


@pytest.fixture(scope='module', params=generate_invalid_event_fixture_params())
def invalid_event_corpus_item(request):
    request.param['file'] = open(request.param['path'])
    return request.param


def test_parse_invalid_structure(invalid_structure_corpus_item):
    e = None
    try:
        with EDXMLPullParser() as parser:
            # Note that the namespace-less 'without-namespace' tag is used
            # for foreign elements in the test corpus.
            parser.parse(invalid_structure_corpus_item['file'], ('without-namespace',))
    except EDXMLValidationError as ex:
        # TODO: We should raise and catch more specific exceptions here:
        #       Introduce InvalidEdxmlStructureError
        #       Introduce InvalidEdxmlOntologyError
        #       Introduce InvalidEdxmlEventError
        e = ex

    # Parser must have raised a validation error.
    assert e is not None


def test_parse_invalid_ontology(invalid_ontology_corpus_item):
    e = None
    try:
        with EDXMLPullParser() as parser:
            parser.parse(invalid_ontology_corpus_item['file'])
    except EDXMLValidationError as ex:
        # TODO: We should raise and catch more specific exceptions here:
        #       Introduce InvalidEdxmlStructureError
        #       Introduce InvalidEdxmlOntologyError
        #       Introduce InvalidEdxmlEventError
        e = ex

    # Parser must have raised a validation error.
    assert e is not None


def test_parse_invalid_event(invalid_event_corpus_item):
    e = None
    try:
        with EDXMLPullParser() as parser:
            parser.parse(invalid_event_corpus_item['file'])
    except EDXMLValidationError as ex:
        # TODO: We should raise and catch more specific exceptions here:
        #       Introduce InvalidEdxmlStructureError
        #       Introduce InvalidEdxmlOntologyError
        #       Introduce InvalidEdxmlEventError
        e = ex

    # Parser must have raised a validation error.
    assert e is not None
