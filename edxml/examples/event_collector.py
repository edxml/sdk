import os

from edxml.miner.knowledge import KnowledgeBase, KnowledgePullParser


# Parse some EDXML data into a knowledge base.
knowledge = KnowledgeBase()
parser = KnowledgePullParser(knowledge)
parser.parse(os.path.dirname(__file__) + '/input.edxml')

# Now mine concepts using automatic seed selection.
parser.mine()

# In case events were parsed that provide a description for some
# object value, we can fetch it from the knowledge base.
names = knowledge.get_descriptions_for('some.object.type', 'some value')
