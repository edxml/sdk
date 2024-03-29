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
from glob import glob

import pytest

from edxml import EDXMLPullParser
from edxml.error import EDXMLValidationError, EDXMLOntologyValidationError, EDXMLEventValidationError
from edxml_test_corpus import CORPUS_PATH

# List of corpus directories corresponding to the EDXML
# versions that we support.
versions = ['3/3.0/3.0.0']

# This glob pattern can be used to select a subset of
# files that will be tested, which may be useful when
# trouble shooting failing tests
file_glob = '*.edxml'


def generate_invalid_structure_fixture_params():
    params = []
    for version_dir in versions:
        path = CORPUS_PATH + version_dir + '/invalid/structure/'
        for filename in os.listdir(path):
            if path + filename in glob(path + file_glob):
                params.append({'path': path + filename})
    return params


def generate_invalid_ontology_fixture_params():
    params = []
    for version_dir in versions:
        path = CORPUS_PATH + version_dir + '/invalid/ontology/'
        for filename in os.listdir(path):
            if path + filename in glob(path + file_glob):
                params.append({'path': path + filename})
    return params


def generate_invalid_event_fixture_params():
    params = []
    for version_dir in versions:
        path = CORPUS_PATH + version_dir + '/invalid/event/'
        for filename in os.listdir(path):
            if path + filename in glob(path + file_glob):
                params.append({'path': path + filename})
    return params


@pytest.fixture(scope='module', params=generate_invalid_structure_fixture_params())
def invalid_structure_corpus_item(request):
    request.param['file'] = open(request.param['path'], 'rb')
    return request.param


@pytest.fixture(scope='module', params=generate_invalid_ontology_fixture_params())
def invalid_ontology_corpus_item(request):
    request.param['file'] = open(request.param['path'], 'rb')
    return request.param


@pytest.fixture(scope='module', params=generate_invalid_event_fixture_params())
def invalid_event_corpus_item(request):
    request.param['file'] = open(request.param['path'], 'rb')
    return request.param


def test_parse_invalid_structure(invalid_structure_corpus_item):
    e = None
    try:
        with EDXMLPullParser() as parser:
            # Note that the namespace-less 'without-namespace' tag is used
            # for foreign elements in the test corpus.
            parser.parse(invalid_structure_corpus_item['file'], ('without-namespace',))
    except EDXMLValidationError as ex:
        e = ex

    # Parser must have raised a validation error.
    assert e is not None


def test_parse_invalid_ontology(invalid_ontology_corpus_item):
    e = None
    try:
        with EDXMLPullParser() as parser:
            parser.parse(invalid_ontology_corpus_item['file'])
    except EDXMLOntologyValidationError as ex:
        e = ex

    # Parser must have raised a validation error.
    assert e is not None


def test_parse_invalid_event(invalid_event_corpus_item):
    e = None
    try:
        with EDXMLPullParser() as parser:
            parser.parse(invalid_event_corpus_item['file'])
    except EDXMLEventValidationError as ex:
        e = ex

    # Parser must have raised a validation error.
    assert e is not None
