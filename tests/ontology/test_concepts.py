from edxml.ontology import Concept


def test_generate_generalizations():
    assert list(Concept.generate_generalizations('a.b.c')) == ['a.b', 'a']
