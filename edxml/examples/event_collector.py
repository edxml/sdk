import os

from edxml.miner import EventCollector, GraphConstructor
from edxml.miner.graph import ConceptInstanceGraph


# Construct graph.
graph = ConceptInstanceGraph()
constructor = GraphConstructor(graph)
EventCollector(constructor).parse(os.path.dirname(__file__) + '/input.edxml')

# Now mine it (automatic seed selection).
graph.mine()
results = graph.extract_result_set()
