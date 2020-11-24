from edxml.miner.graph import ConceptInstanceGraph
from edxml.miner.node import EventObjectNode
from edxml.ontology import EventType, Ontology


def attach_concept_property(event_type, name, concept_name):
    prop = event_type.create_property(name, object_type_name='a')
    return prop.identifies(concept_name)


def mine(nodes, min_confidence=0.1, auto_mine=False):
    graph = ConceptInstanceGraph()

    if not auto_mine:
        # First node is the seed
        seed = next(iter(nodes))
    else:
        seed = None

    # Add all nodes
    for node in nodes:
        graph.add(node)

    # We clear the state of the graph and all of its nodes
    # and edges in case this is not the first time we mine it.
    graph.reset()

    graph.mine(seed, min_confidence)

    result = graph.extract_result_set()

    return result


def mine_concept(nodes, min_confidence=0.1, auto_mine=False):
    result = mine(nodes, min_confidence, auto_mine)
    # Return the first concept found by the mining process
    return next(iter(result.concepts.values()))


def mine_concepts(nodes, min_confidence=0.1, auto_mine=False):
    result = mine(nodes, min_confidence, auto_mine)
    # Return all concepts found by the mining process
    return result.concepts


def test_shared_object_inference_follows_specialized_concept():
    o = Ontology()
    o.create_object_type(name='a')

    type_a = EventType(o, name='a')
    type_b = EventType(o, name='b')

    # Create a property on both event types. One of the concepts
    # is a specialization of the other.
    type_a_c1 = attach_concept_property(type_a, name='a', concept_name='c1')
    type_b_c12 = attach_concept_property(type_b, name='a', concept_name='c1.2')

    # Create nodes representing two events sharing a single object value.
    node_a = EventObjectNode('e1', type_a_c1, object_type_name='a', value='value', confidence=10)
    node_b = EventObjectNode('e2', type_b_c12, object_type_name='a', value='value', confidence=10)

    # Since the shared object is associated with the same generalized concept,
    # in both events we expect the mining process to take the jump from one
    # event to the other. The resulting concept attribute should be backed by
    # both nodes.

    concept = mine_concept([node_a, node_b])

    assert len(concept.attributes[0].nodes) == 2


def test_shared_object_inference_ignores_unrelated_concept():
    o = Ontology()
    o.create_object_type(name='a')
    o.create_concept(name='c1')
    o.create_concept(name='c2')

    type_a = EventType(o, name='a')
    type_b = EventType(o, name='b')

    type_a_c1 = attach_concept_property(type_a, name='a', concept_name='c1')
    type_b_c2 = attach_concept_property(type_b, name='a', concept_name='c2')

    # Create nodes representing two events sharing a single object value.
    node_a = EventObjectNode('e1', type_a_c1, object_type_name='a', value='value', confidence=10)
    node_b = EventObjectNode('e2', type_b_c2, object_type_name='a', value='value', confidence=10)

    # Since both shared objects are associated with unrelated concepts,
    # we expect the resulting concept attribute to be backed by just the
    # seed.

    concept = mine_concept([node_a, node_b])

    assert len(concept.attributes[0].nodes) == 1


def test_heterogeneous_concepts():
    o = Ontology()
    o.create_object_type(name='a')
    o.create_concept(name='c1')
    o.create_concept(name='c2')

    # Epsilon is the numerical error margin for comparing confidences.
    epsilon = 1e-6

    # This is the confidence of the intra-concept relation that we will use.
    rel_confidence = 2

    # We prepare a reasoning path starting at an event e1 which has a property
    # associated with concept c1. Event e1 has an object value for it: 'a'. The
    # property is intra-related to another property which is associated with
    # concept c2. Event e1 has an object value for that related property
    # as well: 'b'. Object value 'b' is shared with another event: 'e2'.
    #
    # The reasoning path looks like this:
    #
    # Inference:       inter       shared
    # Event:     e1 ---------> e1 --------> e2
    # Concept:   c1 ---------> c2 --------> c2
    # Value:     a  ---------> b  --------> b
    #
    # While object value 'b' is associated with a concept that is completely
    # different from the initial seed concept, we do expect the mining process
    # to add it to the concept: From the intra-concept relation it should infer
    # that the concept that is being mined is an instance of both.

    type_a = EventType(o, name='a')
    type_b = EventType(o, name='b')

    type_a_p1_c1 = attach_concept_property(type_a, name='p1', concept_name='c1')
    type_a_p2_c2 = attach_concept_property(type_a, name='p2', concept_name='c2')
    type_b_p1_c2 = attach_concept_property(type_b, name='p1', concept_name='c2')

    p1 = type_a.get_properties()['p1']

    # The intra-concept relation enables inferring that a concept instance of c1
    # is also an instance of c2 with a confidence of 2/10.
    relation_p1_p2 = p1.relate_intra('related to', 'p2', confidence=rel_confidence)

    node_a = EventObjectNode('e1', type_a_p1_c1, object_type_name='a', value='a', confidence=10)
    node_b = EventObjectNode('e1', type_a_p2_c2, object_type_name='a', value='b', confidence=10)
    node_c = EventObjectNode('e2', type_b_p1_c2, object_type_name='a', value='b', confidence=10)

    node_a.link_relation(node_b, relation_p1_p2)

    # Mine using node a as seed using a confidence threshold that is just below what is
    # needed for inference to use the intra-concept relation (confidence 2/10) but too high
    # to use the inferred concept c2 (again confidence 2/10) to jump from e1 to e2.
    concept = mine_concept([node_a, node_b, node_c], min_confidence=0.1 * rel_confidence - epsilon)

    attr_b = next(attr for attr in concept.attributes if attr.value == 'b')

    # As a result we expect the attribute with object value 'b' to be backed by the node from e1 only.
    assert len(attr_b.nodes) == 1

    # The attribute is confirmed by one node having confidence 2/10
    assert attr_b.concept_names == {'c2': 1.0 - (1.0 - 0.2)}

    # Mine again, this time using a confidence threshold that is just below what is
    # needed for inference to use the intra-concept relation (confidence 2/10) and use
    # the inferred concept c2 (again confidence 2/10) to jump from e1 to e2.
    concept = mine_concept([node_a, node_b, node_c], min_confidence=pow(0.1 * rel_confidence, 2) - epsilon)

    attr_b = next(attr for attr in concept.attributes if attr.value == 'b')

    # As a result we expect the attribute with object value 'b' to be backed by the nodes from both events.
    assert len(attr_b.nodes) == 2

    # The attribute is confirmed by both nodes from e2, each having confidence 2/10
    assert attr_b.concept_names == {'c2': 1.0 - (1.0 - 0.2) * (1.0 - 0.2)}


def test_auto_mine():
    o = Ontology()
    o.create_object_type(name='a')
    o.create_concept(name='c1')

    type_a = EventType(o, name='a')

    type_a_p1_c1 = attach_concept_property(type_a, name='p1', concept_name='c1')
    type_a_p2_c2 = attach_concept_property(type_a, name='p2', concept_name='c1')

    node_a = EventObjectNode('e1', type_a_p1_c1, object_type_name='a', value='a', confidence=10)
    node_b = EventObjectNode('e1', type_a_p2_c2, object_type_name='a', value='b', confidence=9)

    # Mine using node a as seed using a confidence threshold that is just below what is
    # needed for inference to use the intra-concept relation (confidence 2/10) but too high
    # to use the inferred concept c2 (again confidence 2/10) to jump from e1 to e2.
    assert len(mine_concepts([node_a, node_b], auto_mine=True)) == 2
