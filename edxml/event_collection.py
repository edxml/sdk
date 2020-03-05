from io import BytesIO
from collections import defaultdict
from typing import Dict, List

import edxml
from edxml.ontology import Ontology


class EventCollection(list):
    """
    Class representing a collection of EDXML events. It is
    an extension of the list type and can be used like any
    other list.
    """
    def __init__(self, events=(), ontology=None):
        """
        Creates a new event collection, optionally initializing it with
        events and an ontology.

        Args:
            events (Iterable[edxml.event.EDXMLEvent]): Initial event collection
            ontology (edxml.ontology.Ontology): Corresponding ontology
        """
        self._ontology = Ontology() if ontology is None else ontology
        super(EventCollection, self).__init__(events)

    def extend(self, iterable):
        if isinstance(iterable, EventCollection):
            self._ontology.update(iterable._ontology)
        super(EventCollection, self).extend(iterable)

    def create_dict_by_hash(self):
        """
        Creates a dictionary mapping sticky hashes to event collections
        containing the events that have that hash. The hashes are
        represented as hexadecimal strings.

        Returns:
            Dict[str, EventCollection]
        """
        hash_dict = defaultdict(EventCollection)  # type: Dict[str, EventCollection]
        for event in self:  # type: edxml.event.EDXMLEvent
            hash_dict[event.compute_sticky_hash(self._ontology)].append(event)
        return hash_dict

    def is_equivalent_of(self, other):
        """
        Compares the collection with another specified collection. It
        returns True in case the two collections are equivalent, i.e.
        there are no semantic differences. For example, when one
        collection contains two instances of the same logical event
        while the other collection contains the result of merging the
        two events then there is no difference. Ordering of events or
        properties within an event are also irrelevant and do not
        result in any differences either.

        Args:
            other (EventCollection): Another event collection

        Returns:
            bool
        """
        if len(self) != len(other):
            return False

        if self._ontology != other._ontology:
            return False

        self_dict = self.create_dict_by_hash()
        other_dict = other.create_dict_by_hash()

        for hash_string, events in self_dict.items():
            if hash_string not in other_dict:
                return False

            other_events = other_dict[hash_string]
            if len(events) > 1:
                events = events.resolve_collisions()
            if len(other_events) > 1:
                other_events = other_events.resolve_collisions()

            event = events.pop()
            other_event = other_events.pop()

            if event != other_event:
                return False

        return True

    def set_ontology(self, ontology):
        """
        Associates the evens in the collection to the
        specified EDXML ontology.

        Args:
            ontology (edxml.ontology.Ontology):

        Returns:
            edxml.EventCollection
        """
        self._ontology = ontology
        return self

    def resolve_collisions(self):
        """
        Returns a new EventCollection that contains only a
        single instance of each logical event in this collection.
        All input event instances that share a sticky hash are merged
        into a single output event.

        Returns:
            edxml.EventCollection

        """
        hash_dict = defaultdict(list)  # type: Dict[str, List[edxml.event.EDXMLEvent]]
        for event in self:  # type: edxml.event.EDXMLEvent
            hash_dict[event.compute_sticky_hash(self._ontology)].append(event)

        result = EventCollection(ontology=self._ontology)
        for events in self.create_dict_by_hash().values():
            if len(events) < 2:
                result.append(events.pop())
                continue
            first = events.pop(0)
            first.merge_with(events, self._ontology)
            result.append(first)

        return result

    @classmethod
    def from_edxml(cls, edxml_data, foreign_element_tags=()):
        """
        Parses EDXML data and returns a new EventSet
        containing the events and ontology information from
        the EDXML data.

        Foreign elements are ignored by default. Optionally, tags
        of foreign elements can be specified allowing the parser
        to process them. The tags must prepend the namespace in
        James Clark notation. Example:

        ['{http://some/foreign/namespace}tag']

        Args:
            edxml_data (bytes): The EDXML data
            foreign_element_tags (Tuple[str]): Foreign element tags

        Returns:
            EventCollection:

        """
        class Parser(edxml.EDXMLPullParser):
            def __init__(self, events):
                super(Parser, self).__init__()
                self.event_set = events

            def _parsed_ontology(self, parsed_ontology):
                self.event_set._ontology.update(parsed_ontology)

            def _parsed_event(self, event):
                self.event_set.append(event)

        event_set = EventCollection()
        event_set._ontology = edxml.ontology.Ontology()

        input_file = BytesIO(edxml_data)
        parser = Parser(event_set)
        parser.parse(input_file, foreign_element_tags)

        return event_set

    def to_edxml(self):
        """
        Returns a string containing the EDXML representation of
        the events in the collection.

        Returns:
            bytes:

        """
        if self._ontology is None:
            raise RuntimeError("Event collection contains no ontology, generating EDXML output is not possible.")

        edxml_data = b''

        writer = edxml.EDXMLWriter()
        edxml_data += writer.add_ontology(self._ontology)

        for event in self:
            edxml_data += writer.add_event(event)

        return edxml_data + writer.close()

    def filter_type(self, event_type_name):
        """
        Returns a new event set containing the subset of
        events of specified event type.

        Args:
            event_type_name (str):

        Returns:
            EventCollection:

        """
        return EventCollection([e for e in self if e.get_type_name() == event_type_name])