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
import re

from edxml.miner import EventCollector, GraphConstructor
from edxml.miner.graph import ConceptInstanceGraph
from edxml.miner.graph.visualize import graphviz_concepts, graphviz_nodes
from edxml.miner.result import MinedConceptInstanceCollection


def get_mining_result() -> MinedConceptInstanceCollection:
    graph = ConceptInstanceGraph()
    constructor = GraphConstructor(graph)

    EventCollector(constructor).parse(os.path.dirname(__file__) + '/input.edxml')

    graph.mine(min_confidence=0.001)
    return graph.extract_result_set(min_confidence=0.01)


def test_concepts_graph(tmp_path):
    results = get_mining_result()

    os.chdir(tmp_path)
    graphviz_concepts(results).render(filename='concepts', format='png')

    source = open(f"{tmp_path}/concepts", 'r').readlines()

    # We expect to see 4 object nodes
    assert len([line for line in source if re.match(r'.*EventObjectNode[^;]+;-[abcd]" \[label.*', line)]) == 4

    # Concept seeds are displayed in blue and we expect to see 3 of those
    assert len([line for line in source if 'EventObjectNode' in line and 'blue' in line]) == 3

    # We expect one low confidence node due to following the intra-concept relation
    assert len([line for line in source if 'EventObjectNode' in line and 'red' in line]) == 1

    # We expect to see an edge between object values "a" and "b"
    assert len([line for line in source if '-a' in line and '->' in line and '-b' in line]) > 0


def test_nodes_graph(tmp_path):
    results = get_mining_result()

    os.chdir(tmp_path)
    graphviz_nodes(results).render(filename='nodes', format='png')

    source = set(open(f"{tmp_path}/nodes", 'r').readlines())

    # We expect one hub for each event object value
    assert len([line for line in source if 'hub' in line and '->' not in line]) == 4

    # We expect to see 4 object value nodes
    assert len([line for line in source if re.match(r'.*"obj.*[abcd]" \[label.*', line) and '->' not in line]) == 4

    # We expect to see 4 object value hubs
    assert len([line for line in source if re.match(r'.*"hub.*[abcd]" \[label.*', line) and '->' not in line]) == 4

    # Each of the 4 object value nodes should have an edge connecting it to its hub
    assert len([line for line in source if re.match(r'.*[abcd]" -> "hub', line)]) == 4

    # We expect to see the relation between object values "a" and "b" with confidence 0.20
    assert len([line for line in source if 'a" -> ' in line and 'b"' in line and 'rel. 0.20' in line]) == 1
