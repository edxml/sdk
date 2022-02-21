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

"""
This module offers classes for constructing graphs for concept mining.

..  autoclass:: KnowledgePullParser
    :members:
    :show-inheritance:

..  autoclass:: KnowledgePushParser
    :members:
    :show-inheritance:
"""
import edxml
from edxml import EDXMLPullParser, EDXMLPushParser
from edxml.miner import Miner


class KnowledgeParserBase:
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (KnowledgeBase): Knowledge base to use
        """
        self.miner = Miner(knowledge_base)  # type: edxml.miner.Miner
        """
        The Miner instance that is used to feed the EDXML data into
        """

    def _parsed_ontology(self, ontology):
        self.miner.add_ontology(ontology)

    def _parsed_event(self, event):
        self.miner.add_event(event)


class KnowledgePullParser(KnowledgeParserBase, EDXMLPullParser):
    """
    EDXML pull parser that feeds EDXML data into a knowledge base.
    """
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (KnowledgeBase): Knowledge base to use
        """
        EDXMLPullParser.__init__(self)
        KnowledgeParserBase.__init__(self, knowledge_base)


class KnowledgePushParser(KnowledgeParserBase, EDXMLPushParser):
    """
    EDXML push parser that feeds EDXML data into a knowledge base.
    """
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (KnowledgeBase): Knowledge base to use
        """
        EDXMLPushParser.__init__(self)
        KnowledgeParserBase.__init__(self, knowledge_base)
