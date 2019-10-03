# -*- coding: utf-8 -*-

import edxml.transcode

from edxml import EDXMLEvent


class JsonTranscoder(edxml.transcode.Transcoder):

    ATTRIBUTE_MAP = {}
    """
    The ATTRIBUTE_MAP attribute is a dictionary mapping event type names to their
    associated attribute mappings. Each attribute mapping is itself a dictionary
    mapping input record attribute names to EDXML event properties. The map is used to
    automatically populate the properties of the output events produced by the
    generate() method of the JsonTranscoder class. The attribute names may contain dots,
    indicating a subfield or positions within a list, like so::

        {'event-type-name': {'fieldname.0.subfieldname': 'property-name'}}

    Note that the event structure will not be validated until the event is yielded by
    the generate() method. This creates the possibility to add nonexistent properties
    to the attribute map and remove them in the generate() method, which may be convenient
    for composing properties from multiple input record attributes, or for splitting the
    auto-generated event into multiple output events.
    """

    EMPTY_VALUES = {}
    """
    The EMPTY_VALUES attribute is a dictionary mapping input record fields to
    values of the associated property that should be considered empty. As an example,
    the data source might use a specific string to indicate a value that is absent
    or irrelevant, like '-', 'n/a' or 'none'. By listing these values with the field
    associated with an output event property, the property will be automatically
    omitted from the generated EDXML events. Example::

        {'fieldname.0.subfieldname': ('none', '-')}

    Note that empty values are *always* omitted, because empty values are not permitted
    in EDXML event objects.

    """

    def generate(self, record, record_type_name, **kwargs):
        """

        Generates one or more EDXML events from the
        given JSON record, populating it with properties
        using the ATTRIBUTE_MAP class property.

        The JSON record can be passed either as a dictionary,
        an object, a dictionary containing objects or an object
        containing dictionaries. Dictionaries are allowed to contain
        lists or other dictionaries. For objects, the ATTRIBUTE_MAP
        will be used to access its attributes. These attributes
        may in turn be dictionaries, lists or other objects. Using
        dotted notation in ATTRIBUTE_MAP, you can extract pretty much
        everything from anything.

        This method can be overridden to create a generic
        event generator, populating the output events with
        generic properties that may or may not be useful to
        the record specific transcoders. The record specific
        transcoders can refine the events that are generated
        upstream by adding, changing or removing properties,
        editing the event content, and so on.

        Args:
          record (dict, object): Decoded JSON data
          record_type_name (str): The JSON record type
          **kwargs: Arbitrary keyword arguments

        Yields:
          EDXMLEvent:
        """

        properties = {}

        event_type_name = self.TYPE_MAP.get(record_type_name, None)

        for JsonField, PropertyName in self.ATTRIBUTE_MAP[event_type_name].items():
            # Below, we parse dotted notation to find sub-fields
            # in the Json data.

            field_path = JsonField.split('.')
            if len(field_path) > 0:
                try:
                    # Try using the record as a dictionary
                    value = record.get(field_path[0])
                except AttributeError:
                    # That did not work. Try using the record
                    # as an object.
                    try:
                        value = getattr(record, field_path[0])
                    except AttributeError:
                        # That did not work either. Try interpreting
                        # the field as an index into a list.
                        try:
                            value = record[int(field_path[0])]
                        except (ValueError, IndexError):
                            # Field not found in record, try next field.
                            continue
                # Now descend into the record to find the innermost
                # value that the field is referring to.
                for Field in field_path[1:]:
                    try:
                        try:
                            value = value.get(Field)
                        except AttributeError:
                            value = getattr(value, Field)
                    except AttributeError:
                        try:
                            value = value[int(Field)]
                        except (ValueError, IndexError):
                            # Field not found in JSON.
                            value = None
                            break

                if value is not None:
                    empty = ['']
                    empty.extend(self.EMPTY_VALUES.get(JsonField, ()))
                    if type(value) == list:
                        properties[PropertyName] = [
                            v for v in value if v not in empty]
                    elif type(value) == bool:
                        properties[PropertyName] = [
                            'true' if value else 'false']
                    else:
                        properties[PropertyName] = [
                            value] if value not in empty else []

        yield EDXMLEvent(properties, event_type_name)
