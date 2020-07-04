import os
from difflib import unified_diff

import pytest
from glob import glob

from edxml import EventCollection

corpus_path = os.path.dirname(os.path.abspath(__file__)) + '/corpus/valid/merge-multiple-files'

# This glob pattern can be used to select a subset of
# directories that will be tested, which may be useful when
# trouble shooting failing tests
dir_glob = '*'


def generate_valid_merge_sequence_fixture_params():
    params = []
    for test_dir in os.listdir(corpus_path):
        if corpus_path + '/' + test_dir in glob(corpus_path + '/' + dir_glob):
            test_params = {'input_paths': []}
            for filename in os.listdir(corpus_path + '/' + test_dir):
                if filename.startswith('input'):
                    test_params['input_paths'].append(corpus_path + '/' + test_dir + '/' + filename)
                else:
                    test_params['expected_path'] = corpus_path + '/' + test_dir + '/' + filename
            params.append(test_params)

    return params


@pytest.fixture(scope='module', params=generate_valid_merge_sequence_fixture_params())
def corpus_item(request):
    request.param['inputs'] = []
    for path in request.param['input_paths']:
        request.param['inputs'].append(open(path, 'rb'))
    if 'expected_path' in request.param:
        request.param['expected'] = open(request.param['expected_path'], 'rb')
    return request.param


def test_parse_sequence(corpus_item):
    parsed = EventCollection()
    for input_data in corpus_item['inputs']:
        # Note that the {http://foreign/namespace}event tag is used
        # for foreign elements in the test corpus.
        parsed.extend(EventCollection.from_edxml(input_data.read(), ('{http://foreign/namespace}event',)))
    parsed = parsed.resolve_collisions()
    if 'expected' in corpus_item:
        expected = EventCollection.from_edxml(corpus_item['expected'].read())
        try:
            assert parsed.is_equivalent_of(expected) is True
        except AssertionError:
            parsed_edxml = parsed.to_edxml().decode('utf-8')
            expected_edxml = expected.to_edxml().decode('utf-8')
            diff = list(unified_diff(parsed_edxml.split('\n'), expected_edxml.split('\n')))
            raise AssertionError(
                'Merging the following corpus items did not yield expected result:\n\n%s\n\nDifference:\n%s' %
                ('\n'.join(corpus_item['input_paths']), '\n'.join(diff))
            )
