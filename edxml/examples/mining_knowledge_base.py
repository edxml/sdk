import os

from edxml.miner.knowledge import KnowledgeBase
from edxml.miner.parser import KnowledgePullParser


# Parse some EDXML data into a knowledge base.
kb = KnowledgeBase()
parser = KnowledgePullParser(kb)
parser.parse(os.path.dirname(__file__) + '/input.edxml')

# Now mine concept instances using automatic seed selection.
parser.miner.mine()

# See how many concept instances were discovered
num_concepts = len(kb.concept_collection.concepts)
