import os

from edxml.miner import EventCollector, GraphConstructor
from edxml.miner.graph import ConceptInstanceGraph


def test_event_collector():
    graph = ConceptInstanceGraph()
    constructor = GraphConstructor(graph)
    EventCollector(constructor).parse(os.path.dirname(__file__) + '/input.edxml')
    graph.mine()
    results = graph.extract_result_set()
    assert len(results.concepts) == 3

    # Check that we have 4 attributes ('a', 'b', 'c' and 'd')
    attributes = [repr(attr) for concept in results.concepts.values() for attr in concept.attributes]

    assert len(attributes) == 4
    assert 'oa: = a' in attributes
    assert 'oa: = b' in attributes
    assert 'oa: = c' in attributes
    assert 'oa: = d' in attributes

    # The concept instances that contain attributes 'a' and 'd' are related (in both ways)
    related = [repr(related) for concept in results.concepts.values() for related in concept.get_related_concepts()]

    assert len(related) == 2
