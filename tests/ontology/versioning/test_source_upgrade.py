import copy
import pytest

from datetime import datetime
from edxml.ontology import Ontology
from tests.assertions import assert_valid_upgrade, assert_incomparable


def test_different_sources_cannot_be_compared():
    o = Ontology()
    a = o.create_event_source('/a/')
    b = o.create_event_source('/b/')

    # Comparing two sources with different URIs
    # makes no sense and throws an exception.
    with pytest.raises(Exception):
        a > b


def test_copies_are_identical():
    o = Ontology()
    a = o.create_event_source('/a/')

    # Exact copies should be identical.
    assert a == copy.deepcopy(a)


def test_description_upgrade():

    o = Ontology()
    a = o.create_event_source('/a/')
    b = copy.deepcopy(a).set_description('changed').set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_description_upgrade():

    o = Ontology()
    a = o.create_event_source('/a/')

    # We change the description without incrementing the version.
    b = copy.deepcopy(a).set_description('changed')

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


def test_acquisition_date_upgrade():

    o = Ontology()
    a = o.create_event_source('/a/')
    b = copy.deepcopy(a).set_acquisition_date(datetime.strptime('1978-06-17', '%Y-%m-%d')).set_version(2)

    # Now, b should be a valid upgrade of a and vice versa.
    assert_valid_upgrade(a, b)


def test_incompatible_acquisition_date_upgrade():

    o = Ontology()
    a = o.create_event_source('/a/')

    # We change the acquisition date without incrementing the version.
    b = copy.deepcopy(a).set_acquisition_date(datetime.strptime('1978-06-17', '%Y-%m-%d'))

    # The versions are now incompatible and cannot be compared.
    assert_incomparable(a, b)


# We can run pytest directly in our debugger
if __name__ == "__main__":
    # -vv: extra verbose
    # -s: do not capture output
    pytest.main(['-vv', '-s'])
