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

from edxml.transcode import RecordTranscoder
from edxml import EDXMLEvent


class ObjectTranscoder(RecordTranscoder):

    PROPERTY_MAP = {}
    """
    The PROPERTY_MAP attribute is a dictionary mapping event type names to their
    associated property mappings. Each property mapping is itself a dictionary
    mapping input record attribute names to EDXML event properties. The map is used to
    automatically populate the properties of the output events produced by the
    generate() method of the ObjectTranscoder class. The attribute names may contain dots,
    indicating a subfield or positions within a list, like so::

        {'event-type-name': {'fieldname.0.subfieldname': 'property-name'}}

    Mapping field values to multiple event properties is also possible::

        {'event-type-name': {'fieldname.0.subfieldname': ['property', 'another-property']}}

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

    def generate(self, input_object, record_type_name, **kwargs):
        """

        Generates one or more EDXML events from the
        given input record, populating it with properties
        using the PROPERTY_MAP class property.

        When the record transcoder is the fallback transcoder,
        record_type_name will be None.

        The input record can be a dictionary or act like one, it can
        be an object, a dictionary containing objects or an object
        containing dictionaries. Object attributes or dictionary
        items are allowed to contain lists or other objects. The keys
        in the PROPERTY_MAP will be used to access its items or
        attributes. Using dotted notation in PROPERTY_MAP, you can
        extract pretty much everything from anything.

        This method can be overridden to create a generic
        event generator, populating the output events with
        generic properties that may or may not be useful to
        the specific record transcoders. The specific record
        transcoders can refine the events that are generated
        upstream by adding, changing or removing properties,
        editing the event attachments, and so on.

        Args:
          input_object (dict, object): Input object
          record_type_name (Optional[str]): The record type of the input object
          **kwargs: Arbitrary keyword arguments

        Yields:
          EDXMLEvent:
        """

        properties = {}

        if record_type_name not in self.TYPE_MAP:
            raise Exception(
                f"{type(self).__name__} is registered as a transcoder for records of type '{record_type_name}' "
                f"while its TYPE_MAP constant has no corresponding key for that record type."
            )

        event_type_name = self.TYPE_MAP[record_type_name]

        for selector, property_names in self.PROPERTY_MAP[event_type_name].items():

            if not isinstance(property_names, list):
                property_names = [property_names]

            # Below, we parse dotted notation to find sub-fields
            # in the object.

            try:
                field_path = selector.split('.')
            except AttributeError:
                # Field path could be an integer key into a dictionary
                # or a list index.
                field_path = [selector]
            if len(field_path) > 0:
                try:
                    # Try using the record as a dictionary
                    value = input_object.get(field_path[0])
                except AttributeError:
                    # That did not work. Try using the record
                    # as an object.
                    try:
                        value = getattr(input_object, field_path[0])
                    except (TypeError, AttributeError):
                        # That did not work either. Try interpreting
                        # the field as an index into a list.
                        try:
                            value = input_object[int(field_path[0])]
                        except (ValueError, IndexError):
                            # Field not found in record, try next field.
                            continue
                # Now descend into the record to find the innermost
                # value that the field is referring to.
                for field in field_path[1:]:
                    try:
                        try:
                            value = value.get(field)
                        except AttributeError:
                            value = getattr(value, field)
                    except AttributeError:
                        try:
                            value = value[int(field)]
                        except (ValueError, IndexError):
                            # Field not found in object.
                            value = None
                            break

                if value is not None:
                    empty = ['']
                    empty.extend(self.EMPTY_VALUES.get(selector, ()))

                    if type(value) == list:
                        property_values = [v for v in value if v not in empty]
                    elif type(value) == bool:
                        property_values = ['true' if value else 'false']
                    else:
                        property_values = [value] if value not in empty else []

                    for property_name in property_names:
                        properties[property_name] = property_values

        yield EDXMLEvent(self._post_process_properties(event_type_name, properties), event_type_name)
