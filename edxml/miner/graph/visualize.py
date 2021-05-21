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

from edxml.miner.inference import RelationInference
from edxml.miner.node import EventObjectHub
from edxml.util import truncate_string
from graphviz import Digraph


def graphviz_nodes(concepts, graph=None):
    """

    Adds concept instances to a GraphViz directed graph instance and returns it.
    By default a suitable GraphViz instance is generated, using an instance
    created by the caller is also possible.

    The resulting graph is very detailed, showing every single node. As
    such, it is intended to be used for small graphs.

    Args:
        concepts (edxml.miner.result.MinedConceptInstanceCollection): Concept instances
        graph (graphviz.Digraph): GraphViz Digraph instance

    Returns:
        graphviz.Digraph: GraphViz Digraph instance

    """
    graph = graph or Digraph(
        node_attr={
            'fontname': 'sans', 'shape': 'box', 'style': 'rounded'
        },
        edge_attr={'fontname': 'sans'},
        engine='dot',
        graph_attr={'rankdir': 'LR'},
        strict='true'
    )

    for concept in concepts.concepts.values():
        for node in concept.get_nodes().values():
            if node.seed_confidences == {}:
                # Node is not part of any concept instance
                continue

            for edge in node._edges:
                if edge.seeds == set():
                    # Edge is not part of any concept instance
                    continue
                for edge_node in [edge.source, edge.target]:
                    confidences = edge_node.seed_confidences.values()
                    if len(confidences) > 1:
                        confidence_range = "%.2f-%.2f" % (min(confidences), max(confidences))
                    else:
                        confidence_range = "%.2f" % min(confidences)
                    if isinstance(edge_node, EventObjectHub):
                        title = "hub %s (%s)\n%s" % (
                            edge_node.value, confidence_range,
                            truncate_string(edge_node.object_type_name, max_length=12, trunc_head=True)
                        )
                    else:
                        title = "%s (%s)" % (edge_node.value, confidence_range)
                    graph.node(edge_node.id.replace(':', ';'), title)

                if isinstance(edge, RelationInference):
                    label = "rel. %.2f" % edge.confidence
                else:
                    label = "%.2f" % edge.confidence
                graph.edge(str(edge.source.id.replace(':', ';')), str(edge.target.id.replace(':', ';')), label)

    return graph


def graphviz_concepts(concepts, graph=None):
    """
    Adds concept instances to a GraphViz directed graph instance and returns it.
    By default a suitable GraphViz instance is generated, using an instance
    created by the caller is also possible.

    The resulting graph shows the concepts, their attributes and the reasoning
    paths that connect the attributes within the concept. Attributes that are
    shared among multiple concept instances are generally not connected, which
    keeps the graphs simple and readable. An exception is made for ambiguities
    where it is unclear which concept instance an attribute belongs to. A
    heuristic is used to decide what to do.

    Args:
        concepts (edxml.miner.result.MinedConceptInstanceCollection): Concept instances
        graph (graphviz.Digraph): GraphViz Digraph instance

    Returns:
        graphviz.Digraph: GraphViz Digraph instance
    """
    graph = graph or Digraph(
        node_attr={
            'fontname': 'sans',
            'shape': 'box',
            'style': 'rounded,filled',
            'fillcolor': 'white',
            'penwidth': '2',
        },
        edge_attr={
            'fontname': 'sans',
            'color': 'gray80'
        },
        engine='neato',
        graph_attr={
            'rankdir': 'LR',
            'overlap': 'false',
            'outputorder': 'edgesfirst'
        },
        strict='true'
    )

    seeds = []
    confidences = {}
    for seed_id, concept in concepts.concepts.items():
        for attribute in concept.attributes:
            if [node for node in attribute.nodes.values() if node.id == seed_id]:
                # When any of the nodes of an attribute is a seed, we
                # consider all of its nodes to be seeds for the sake
                # of this visualization. We do that because we aggregate
                # on attributes.
                seeds.extend(attribute.nodes.keys())
            # We build a mapping of node ID to the confidence of the
            # attribute that it is part of.
            confidences.update({node_id: attribute.confidence for node_id, node in attribute.nodes.items()})

    for seed_id, concept in concepts.concepts.items():
        for attribute in concept.attributes:
            # While we want to display just one graphviz node for each concept
            # attribute value we cannot suffice to use just one of the
            # object value nodes for each attribute. The reason is that each node
            # may have different edges attached to them. Picking one node means we
            # may be missing edges between nodes.
            for node in attribute.nodes.values():
                _graphviz_add_node_with_edges(graph, seeds, confidences, node, seed_id)

    return graph


def _graphviz_add_node_with_edges(graph, seeds, confidences, node, seed_id):

    _graphviz_add_node(graph, seeds, node, seed_id, confidences[node.id])

    for edge in node._edges:
        if seed_id not in edge.seeds:
            # Edge is not part of current concept instance
            continue
        if not isinstance(edge, RelationInference) or edge.relation.get_type() != 'intra':
            # Edge is not an intra-concept relation.
            continue
        source = edge.source
        target = edge.target
        _graphviz_add_edge(graph, seeds, confidences, source, target, seed_id)


def _graphviz_add_node(graph, seeds, node, seed_id, confidence):
    node_color = _get_node_color(node, seed_id, node.id in seeds, confidence)
    node_title = _get_node_title(node.value, node.concept_association.get_concept_name(), subtitle_trunc_head=True)
    node_id = _get_graphviz_node_id(node, seed_id)

    graph.node(node_id, node_title, color=node_color)


def _graphviz_add_edge(graph, seeds, confidences, source, target, seed_id):

    if seed_id not in source.seed_confidences:
        # source is not part of concept
        return
    if seed_id not in target.seed_confidences:
        # target is not part of concept
        return

    source_node_id = _get_graphviz_node_id(source, seed_id)
    target_node_id = _get_graphviz_node_id(target, seed_id)
    _graphviz_add_node(graph, seeds, source, seed_id, confidences[source.id])
    _graphviz_add_node(graph, seeds, target, seed_id, confidences[target.id])

    graph.edge(source_node_id, target_node_id)


def _get_node_title(title, subtitle=None, title_trunc_head=False, subtitle_trunc_head=False):
    node_title = truncate_string(title, 16, title_trunc_head)
    if subtitle is not None:
        node_title += f"<br/><font point-size='10'>({truncate_string(subtitle, 20, subtitle_trunc_head)})</font>"
    return f"<{node_title}>"


def _get_node_color(node, seed_id, is_seed=False, confidence=None):
    confidence_colors = [
        'red2',
        'red2',
        'orange2',
        'orange2',
        'orange2',
        'gold3',
        'gold3',
        'gold3',
        'forestgreen',
        'forestgreen',
        'forestgreen',
    ]

    confidence = confidence or node.seed_confidences[seed_id]

    # Color nodes by their confidence
    source_color = confidence_colors[int(10 * confidence)]

    # Display the concept seeds in blue
    if is_seed:
        source_color = 'blue'

    return source_color


def _get_graphviz_node_id(node, seed_id):
    # If value of the node has a high confidence as identifier
    # of a concept instance, then it is tightly bound
    # to the concept instance. This means that
    # multiple concept instances may be competing for ownership.
    # We show this by creating a single shared node for it.
    # TODO: The confidence cutoff is arbitrary, make configurable?
    source_node_id = type(node).__name__
    if node.concept_association.get_confidence() > 8:
        source_node_id += f"-{node.attribute_name}-{node.value}"
    else:
        source_node_id += f"-{seed_id}-{node.attribute_name}-{node.value}"

    # Remove characters with special meaning in GraphViz node names
    return source_node_id.replace(':', ';')
