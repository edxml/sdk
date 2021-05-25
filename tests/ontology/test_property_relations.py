from edxml.ontology import Ontology


def test_evaluate_description():
    o = Ontology()
    o.create_object_type('a')

    e = o.create_event_type('a')
    e.create_property('p1', 'a')
    e.create_property('p2', 'a')

    a = e['p1'].relate_to('related to', 'p2').because('[[p1]] relates to [[p2]]')

    assert a.evaluate_description(event_properties={'p1': {'a'}, 'p2': {'b'}}) == 'A relates to b'
