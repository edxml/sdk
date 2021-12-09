import os

from edxml.miner.knowledge import KnowledgeBase, KnowledgePullParser


# Parse some EDXML data into a knowledge base.
knowledge = KnowledgeBase()
parser = KnowledgePullParser(knowledge)
parser.parse(os.path.dirname(__file__) + '/input.edxml')

# Now mine concept instances using automatic seed selection.
parser.mine()

# See how many concept instances were discovered
num_concepts = len(knowledge.concept_collection.concepts)
