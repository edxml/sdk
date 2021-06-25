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

import re
from typing import Dict

import edxml
from .ontology.event_type import EventType
from dateutil import relativedelta
from dateutil.parser import parse, ParserError
from edxml.error import EDXMLOntologyValidationError
from termcolor import colored


class Template(object):

    TEMPLATE_PATTERN = re.compile(r'\[\[[^]]*]]')

    KNOWN_FORMATTERS = (
        'time_span', 'date_time', 'duration', 'merge', 'attachment',
        'boolean_string_choice', 'boolean_on_off', 'boolean_is_is_not', 'empty', 'unless_empty', 'url'
    )

    DATE_TIME_FORMATTERS = ['time_span', 'duration', 'date_time']

    BOOLEAN_FORMATTERS = ['boolean_string_choice', 'boolean_on_off', 'boolean_is_is_not']

    FORMATTER_PROPERTY_COUNTS = {
        'time_span': 2,
        'date_time': 1,
        'duration': 2,
        'boolean_string_choice': 1,
        'boolean_on_off': 1,
        'boolean_is_is_not': 1,
        'empty': 1,
        'attachment': 0,
        'url': 1
    }

    FORMATTER_ARGUMENT_COUNTS = {
        'time_span': 2,
        'DATE': 1,
        'date_time': 2,
        'duration': 2,
        'boolean_string_choice': 3,
        'boolean_on_off': 1,
        'boolean_is_is_not': 1,
        'empty': 1,
        'attachment': 1,
        'url': 2
    }

    def __init__(self, template):
        self._template = template

    def validate(self, event_type, property_names=None):
        """
        Checks if given template is valid for the given event type. By default,
        the template may refer to any of the properties of the event type. This
        may be restricted by passing a custom list of property names.

        Args:
          event_type (edxml.ontology.EventType): The event type
          property_names (Optional[List[str]]):

        Raises:
          EDXMLOntologyValidationError

        """

        if property_names is None:
            properties = event_type.get_properties()
        else:
            properties = {name: prop for name, prop in event_type.get_properties().items() if name in property_names}

        # Test if template grammar is correct, by
        # checking that curly brackets are balanced.
        curly_nestings = {'{': 1, '}': -1}
        nesting = 0
        for curly in [c for c in self._template if c in ['{', '}']]:
            nesting += curly_nestings[curly]
            if nesting < 0:
                raise EDXMLOntologyValidationError('Unbalanced curly brackets')
        if nesting != 0:
            raise EDXMLOntologyValidationError('Unbalanced curly brackets')

        placeholder_strings = re.findall(self.TEMPLATE_PATTERN, self._template)

        for placeholder in placeholder_strings:
            formatter, _ = self._parse_placeholder(placeholder)

            if formatter is not None and formatter not in self.KNOWN_FORMATTERS:
                raise EDXMLOntologyValidationError('Unknown formatter: %s' % formatter)

            property_arguments, other_arguments = self._get_placeholder_arguments(placeholder)

            for property_name in property_arguments:
                if property_name == '':
                    raise EDXMLOntologyValidationError(
                        'Empty property name in %s formatter.' % formatter
                    )
                if property_name not in properties.keys():
                    raise EDXMLOntologyValidationError(
                        'Template refers to a property named "%s" which either do not exist or '
                        'which cannot be used in this template.' % property_name
                    )

            argument_count = self.FORMATTER_ARGUMENT_COUNTS.get(formatter)

            if argument_count is not None and len(property_arguments) + len(other_arguments) != argument_count:
                raise EDXMLOntologyValidationError(
                    'The %s formatter accepts %d arguments, but %d were specified: %s' % (
                        formatter, argument_count, len(property_arguments) + len(other_arguments), placeholder
                    )
                )

            if formatter in self.DATE_TIME_FORMATTERS:
                # Check that both properties are datetime values
                for property_name in property_arguments:
                    if str(properties[property_name].get_data_type()) != 'datetime':
                        raise EDXMLOntologyValidationError(
                             'Time related formatter (%s) used on property (%s) which is not a datetime value.' % (
                                formatter, property_name
                             )
                        )

            if formatter in self.BOOLEAN_FORMATTERS:
                # Check that property is a boolean
                for property_name in property_arguments:
                    if str(properties[property_name].get_data_type()) != 'boolean':
                        raise EDXMLOntologyValidationError(
                            'The %s formatter was used on property %s which is not a boolean.' % (
                                formatter, property_name
                            )
                        )

            if formatter == 'date_time':
                if other_arguments[0] not in [
                    'year', 'month', 'date', 'hour', 'minute', 'second', 'millisecond', 'microsecond'
                ]:
                    raise EDXMLOntologyValidationError(
                        'A date_time formatter uses an unknown accuracy option: "%s".' % other_arguments[0]
                    )

            if formatter == 'attachment':
                if other_arguments[0] not in event_type.get_attachments():
                    raise EDXMLOntologyValidationError(
                        'A attachment formatter refers to event attachment "%s", '
                        'which is not defined.' % other_arguments[0]
                    )

        return self

    def evaluate(self, event_type, event_properties, event_attachments,
                 capitalize=True, colorize=False, ignore_value_errors=False):
        """

        Evaluates the EDXML template of an event type using
        specified event, returning the result. The event_properties and event_attachments
        parameters must be structured in the same way as they are obtained from EDXMLEvent
        instances.

        Optionally, the output can be colorized. At his time this means that,
        when printed on the terminal, the objects in the evaluated string will
        be displayed using bold white characters.

        When rendering of object values fails because the value is not valid for
        its object type an exception is raised unless ignore_value_errors is enabled.

        Args:
          event_type (edxml.ontology.EventType): the event type of the event
          event_properties (Dict[str, Set]): the event properties to use
          event_attachments (Dict[str, Dict[str, str]]): the event attachments to use
          capitalize (bool): Capitalize evaluated template yes or no
          colorize (bool): Colorize output or not
          ignore_value_errors (bool): Ignore object value errors yes or no

        Returns:
          str:
        """

        evaluated = self._process_split_template(
            self._split_template(self._template)[1], event_type, event_properties,
            event_attachments, colorize, ignore_value_errors
        )

        return self._capitalize(evaluated) if capitalize else evaluated

    @classmethod
    def generate_collapsed_templates(cls, event_type: EventType, template, colorize=False):
        """

        Generates a sequence of progressively degraded evaluated templates by
        iteratively omitting object values for the event properties that are
        mentioned in the template.

        On the first iteration, a complete evaluated template is generated,
        without omitting any properties. The last iteration yields a fully
        collapsed template.

        Yields tuples containing two items each. The first item is the set
        of property names that have been omitted. The second item is the
        evaluated template.

        Args:
            event_type (EventType): The associated event type
            template (str): The EDXML template
            colorize (bool): Produce colorized output yes or no

        Yields:
            Tuple[Set, str]:
        """
        properties = {}
        for property_name, event_property in event_type.get_properties().items():
            object_type = event_property.get_object_type()
            if event_property.is_single_valued():
                properties[property_name] = {'some ' + object_type.get_display_name_singular()}
            else:
                properties[property_name] = {'one or more ' + object_type.get_display_name_plural()}

        # Yield a complete evaluated template first.
        yield set(), Template(template).evaluate(
            event_type, properties, {}, colorize=colorize, ignore_value_errors=True
        )

        while template != '':
            start, end, empty_prop_sets = cls._get_innermost_collapsing_property_sets(event_type, template)
            for empty_prop_set in empty_prop_sets:
                # Create a new event with one or more omitted properties.
                # On each iteration, the event gets less detailed.
                partial_props = dict(properties)
                for empty_prop in empty_prop_set:
                    if empty_prop in partial_props:
                        del partial_props[empty_prop]
                properties = partial_props
                yield empty_prop_set, Template(template).evaluate(
                    event_type, properties, {}, colorize=colorize, ignore_value_errors=True
                )

            # Collapse inner scope and repeat.
            collapsed = template[:start] + Template(template[start:end]).evaluate(
                    event_type, properties, {}, colorize=colorize, capitalize=False, ignore_value_errors=True
                ) + template[end:]

            if collapsed == template:
                # No more scopes in template. We are done.
                return

            # Iterate using collapsed template.
            template = collapsed

    @classmethod
    def _get_innermost_collapsing_property_sets(cls, event_type, template):
        """

        Finds sets of properties that, when its object values are omitted,
        trigger a collapse in the deepest available scope of the template.

        Args:
            event_type (EventType): The event type
            template (str): The template

        Returns:
            Tuple:
        """
        _, offset, _, substring = cls._find_innermost_part(cls._split_template(template)[1])

        placeholders = re.findall(r'\[\[[^]]*]]', substring)
        return (
            offset,
            offset + len(substring),
            cls._find_collapsable_property_sets(placeholders, event_type)
        )

    @classmethod
    def _find_innermost_part(cls, split_template, initial_level=0, initial_offset=0):
        """

        Finds the part of a template that is the most deeply nested in terms of
        scopes. The can either dig up some sub-scope or the full template in case
        no sub-scopes are present.

        Args:
            split_template (List): The split template
            initial_level (int): Initial depth
            initial_offset (int): Initial offset into template string

        Returns:
            Tuple:
        """
        deepest_level = initial_level
        deepest_part = None
        deepest_offset = 0
        offset = initial_offset
        for part in split_template:
            if isinstance(part, list):
                # We found a sub-scope. Recurse to search deeper.
                deeper_level, deeper_offset, offset, deeper_part = cls._find_innermost_part(
                    part, initial_level + 1, offset
                )
                # Note that the curly brackets are stripped
                # from split templates. Here, we compensate
                # for that.
                offset += 1
                deeper_part = '{' + deeper_part + '}'
            else:
                deeper_level = initial_level
                deeper_offset = offset
                deeper_part = part
                offset += len(part)

            if deeper_level > deepest_level or deepest_part is None:
                # We found a part that is at nested
                # deeper. Or, if this is the first part
                # we looked at so fat, we will accept anything.
                deepest_level = deeper_level
                deepest_part = deeper_part
                deepest_offset = deeper_offset

        return deepest_level, deepest_offset, offset, deepest_part

    @classmethod
    def _find_collapsable_property_sets(cls, placeholders, event_type):
        """

        Returns a list of sets of property names from specified placeholders
        that will trigger a collapse when its values are omitted.

        Args:
            placeholders (List[str]): The placeholders
            event_type (EventType): The event type

        Returns:
            List[Set]:
        """
        mandatory_properties = event_type.get_mandatory_property_names()

        collapsable_property_sets = []
        for placeholder in placeholders:
            formatter, arguments = cls._parse_placeholder(placeholder)
            if formatter == 'empty':
                # Cannot collapse
                continue
            if formatter == 'unless_empty':
                # Collapses when all specified properties empty.
                if any(arg for arg in arguments[:-1] if arg in mandatory_properties):
                    # There are mandatory properties amongst the arguments,
                    # so no collapse can occur.
                    continue
                collapsable_property_sets.append(set(arguments[:-1]))
            elif formatter == 'merge':
                # Can only collapse when all of its
                # arguments are empty properties
                if any(arg for arg in arguments if arg in mandatory_properties):
                    # There are mandatory properties amongst the arguments,
                    # so no collapse can occur.
                    continue
                collapsable_property_sets.append(set(arguments))
            else:
                if formatter is None:
                    properties = arguments
                else:
                    properties = arguments[:cls.FORMATTER_PROPERTY_COUNTS[formatter]]
                collapsable_property_sets.extend({prop, } for prop in properties if prop not in mandatory_properties)

        return collapsable_property_sets

    @classmethod
    def _split_template(cls, template, offset=0):

        elements = []
        length = len(template)

        while offset < length:
            pos1 = template.find('{', offset)
            pos2 = template.find('}', offset)
            if pos1 == -1:
                # There are no more sub-strings, Find closing bracket.
                if pos2 == -1:
                    # No closing bracket either, which means that the
                    # remaining part of the string is one element.
                    # lacks brackets.
                    substring = template[offset:length]
                    offset = length
                    elements.append(substring)
                else:
                    # Found closing bracket. Add substring and return
                    # to caller.
                    substring = template[offset:pos2]
                    offset = pos2 + 1
                    elements.append(substring)
                    break
            else:
                # We found an opening bracket.

                if pos2 == -1:
                    # No closing bracket
                    # Give up.
                    offset = length
                else:
                    # We also found a closing bracket.

                    if pos1 < pos2:
                        # Opening bracket comes first, which means we should
                        # iterate.
                        substring = template[offset:pos1]
                        offset = pos1 + 1

                        elements.append(substring)
                        offset, parsed = cls._split_template(template, offset)
                        elements.append(parsed)
                    else:
                        # closing bracket comes first, which means we found
                        # an innermost substring. Add substring and return
                        # to caller.
                        substring = template[offset:pos2]
                        offset = pos2 + 1
                        elements.append(substring)
                        break

        return offset, elements

    @staticmethod
    def _format_time_duration(date_time_a, date_time_b):
        delta = relativedelta.relativedelta(date_time_b, date_time_a)

        if delta.minutes > 0:
            if delta.hours > 0:
                if delta.days > 0:
                    if delta.months > 0:
                        if delta.years > 0:
                            return '%d years, %d months, %d days, %d hours, %d minutes and %d seconds' % \
                                   (delta.years, delta.months, delta.days,
                                    delta.hours, delta.minutes, delta.seconds)
                        else:
                            return '%d months, %d days, %d hours, %d minutes and %d seconds' % \
                                   (delta.months, delta.days, delta.hours,
                                    delta.minutes, delta.seconds)
                    else:
                        return '%d days, %d hours, %d minutes and %d seconds' % \
                               (delta.days, delta.hours,
                                delta.minutes, delta.seconds)
                else:
                    return '%d hours, %d minutes and %d seconds' % \
                           (delta.hours, delta.minutes, delta.seconds)
            else:
                return '%d minutes and %d seconds' % \
                       (delta.minutes, delta.seconds)
        else:
            return '%d.%d seconds' % \
                   (delta.seconds, delta.microseconds)

    @classmethod
    def _process_simple_placeholder_string(
            cls, event_type, string, event_object_values, event_attachments, colorize, ignore_value_errors
    ):
        """

        Args:
            event_type (edxml.ontology.EventType):
            string (str):
            event_object_values (Dict[str, set]):
            event_attachments (Dict[str, Dict[str, str]]):
            colorize (bool):
            ignore_value_errors (bool):

        Returns:
            str
        """

        replacements = {}

        # Match on placeholders like "[[DATETIME:datetime,minute]]", creating
        # groups of the strings in between the placeholders and the
        # placeholders themselves, with and without brackets included.
        placeholders = re.findall(r'(\[\[([^]]*)]])', string)

        property_data_types = {}  # type: Dict[str, edxml.ontology.DataType]

        # Format object values based on their data type to make them
        # more human friendly.
        for property_name, values in event_object_values.items():
            property_data_types[property_name] = event_type[property_name].get_data_type()
            if property_data_types[property_name].get_family() == 'number':
                if property_data_types[property_name].get_split()[1] in ('float', 'double'):
                    # Floating point numbers are normalized in scientific notation,
                    # here we format it to whatever is the most suitable for the value.
                    try:
                        event_object_values[property_name] = {'%f' % float(value) for value in values}
                    except ValueError:
                        if not ignore_value_errors:
                            raise
                        # Object value is not valid. Just render the values as strings.
                        event_object_values[property_name] = {str(value) for value in values}

        for placeholder in placeholders:

            object_strings = []
            try:
                formatter, argument_string = placeholder[1].split(':', 1)
                arguments = argument_string.split(',')
            except ValueError:
                # No formatter present.
                formatter = None
                arguments = placeholder[1].split(',')

            if formatter == 'time_span':

                try:
                    # Note that we use lexicographic sorting here.
                    date_time_start = min(event_object_values.get(arguments[0], []))
                    date_time_end = min(event_object_values.get(arguments[1], []))
                except ValueError:
                    # An argument was missing or a property is missing an object
                    # value. This implies that we must return an empty string.
                    return ''

                try:
                    span = parse(date_time_start).isoformat(' '), parse(date_time_end).isoformat(' ')
                except ParserError:
                    if not ignore_value_errors:
                        raise
                    # Not a valid date string. Just render it as-is.
                    span = date_time_start, date_time_end
                object_strings.append(
                    'between %s and %s' % span
                )

            elif formatter == 'duration':

                try:
                    # Note that we use lexicographic sorting here.
                    date_time_start = min(event_object_values.get(arguments[0], []))
                    date_time_end = min(event_object_values.get(arguments[1], []))
                except ValueError:
                    # An argument was missing or a property is missing an object
                    # value. This implies that we must return an empty string.
                    return ''

                try:
                    duration = cls._format_time_duration(parse(date_time_start), parse(date_time_end))
                except ParserError:
                    if not ignore_value_errors:
                        raise
                    # Not a valid date string. Just render it as-is.
                    duration = f"the time that passed between {date_time_start} and {date_time_end}"

                object_strings.append(duration)

            elif formatter == 'date_time':

                for object_value in event_object_values.get(arguments[0], []):
                    try:
                        date_time = parse(object_value)
                    except ParserError:
                        if not ignore_value_errors:
                            raise
                        # Not a valid date string. Just render it as-is.
                        object_strings.append(object_value)
                        continue
                    if arguments[1] == 'microsecond':
                        object_strings.append(date_time.strftime('%A, %B %d %Y at %H:%M:%S.%fh'))
                    elif arguments[1] == 'millisecond':
                        object_strings.append(
                            date_time.strftime('%A, %B %d %Y at %H:%M:%S.') +
                            date_time.strftime('%f')[:3] + 'h'
                        )
                    elif arguments[1] == 'second':
                        object_strings.append(date_time.strftime('%A, %B %d %Y at %H:%M:%Sh'))
                    elif arguments[1] == 'minute':
                        object_strings.append(date_time.strftime('%A, %B %d %Y at %H:%Mh'))
                    elif arguments[1] == 'hour':
                        object_strings.append(date_time.strftime('%A, %B %d %Y at %Hh'))
                    elif arguments[1] == 'date':
                        object_strings.append(date_time.strftime('%A, %B %d %Y'))
                    elif arguments[1] == 'month':
                        object_strings.append(date_time.strftime('%B %Y'))
                    else:  # year
                        object_strings.append(date_time.strftime('%Y'))

            elif formatter == 'url':

                property_name, target_name = arguments
                for object_value in event_object_values.get(arguments[0], []):
                    object_strings.append('%s (%s)' % (target_name, object_value))

            elif formatter == 'merge':

                for property_name in arguments:
                    for object_value in event_object_values.get(property_name, []):
                        object_strings.append(object_value)

            elif formatter == 'boolean_string_choice':

                property_name, true, false = arguments
                for object_value in event_object_values.get(arguments[0], []):
                    if object_value == 'true':
                        object_strings.append(true)
                    elif object_value == 'false':
                        object_strings.append(false)
                    else:
                        if not ignore_value_errors:
                            raise ValueError(f"Invalid boolean value in property {property_name}: {object_value}")
                        # Not a valid object value, we have no way
                        # of picking one or the other.
                        object_strings.append(f"{true} or {false}")

            elif formatter == 'boolean_on_off':

                for object_value in event_object_values.get(arguments[0], []):
                    if object_value == 'true':
                        object_strings.append('on')
                    elif object_value == 'false':
                        object_strings.append('off')
                    else:
                        if not ignore_value_errors:
                            raise ValueError(f"Invalid boolean value in property {arguments[0]}: {object_value}")
                        # Not a valid object value, we have no way
                        # of picking one or the other.
                        object_strings.append('on or off')

            elif formatter == 'boolean_is_is_not':

                for object_value in event_object_values.get(arguments[0], []):
                    if object_value == 'true':
                        object_strings.append('is')
                    elif object_value == 'false':
                        object_strings.append('is not')
                    else:
                        if not ignore_value_errors:
                            raise ValueError(f"Invalid boolean value in property {arguments[0]}: {object_value}")
                        # Not a valid object value, we have no way
                        # of picking one or the other.
                        object_strings.append('is or is not')

            elif formatter == 'empty':

                property_name = arguments[0]
                if property_name not in event_object_values or len(event_object_values[property_name]) == 0:
                    # Property has no object, use the second formatter argument
                    # in stead of the object value itself.
                    object_strings.append(arguments[1])

            elif formatter == 'attachment':
                for attachment_value in event_attachments.get(arguments[0], {}).values():
                    object_strings.append('\n\n' + attachment_value + '\n\n')

            elif formatter == 'unless_empty':

                not_empty_string = arguments.pop()
                if [value for property_name in arguments for value in event_object_values.get(property_name, [])]:
                    object_strings.append(not_empty_string)

            else:

                # String has no associated formatter but maybe the the data
                # type implies an appropriate value format.
                property_name = arguments[0]
                if property_name in property_data_types and property_data_types[property_name].type == 'geo:point':
                    for object_value in event_object_values.get(property_name, []):
                        try:
                            lat, long = object_value.split(',')
                            degrees = int(float(lat))
                            minutes = int((float(lat) - degrees) * 60.0)
                            seconds = int((float(lat) - degrees - (minutes / 60.0)) * 3600.0)

                            lat_long = '%d°%d′%d %s″' % (degrees, minutes, seconds, 'N' if degrees > 0 else 'S')

                            degrees = int(float(long))
                            minutes = int((float(long) - degrees) * 60.0)
                            seconds = int((float(long) - degrees - (minutes / 60.0)) * 3600.0)

                            lat_long += ' %d°%d′%d %s″' % (degrees, minutes, seconds, 'E' if degrees > 0 else 'W')
                        except ValueError:
                            if not ignore_value_errors:
                                raise
                            # Not a valid object value, just print it as-is.
                            lat_long = object_value

                        object_strings.append(lat_long)
                else:
                    object_strings.extend(event_object_values.get(property_name, []))

            if len(object_strings) > 0:
                if len(object_strings) > 1:
                    # If one property has multiple objects,
                    # list them all.
                    if ''.join(object_strings) != '':
                        last_object_value = object_strings.pop()
                        if colorize:
                            object_string = ', '.join(
                                colored(object_string, 'white', attrs=['bold']) for object_string in object_strings
                            ) + ' and ' + colored(last_object_value, 'white', attrs=['bold'])
                        else:
                            object_string = ', '.join(object_strings) + ' and ' + last_object_value
                    else:
                        object_string = ''
                else:
                    if colorize and object_strings[0] != '':
                        object_string = colored(object_strings[0], 'white', attrs=['bold'])
                    else:
                        object_string = object_strings[0]
            else:
                object_string = ''

            replacements[placeholder[0]] = object_string

        # Return template where all placeholders are replaced
        # by the actual (formatted) object values

        for placeholder, replacement in replacements.items():
            if replacement == '':
                # Placeholder produces empty string, which
                # implies that we must produce an empty result.
                return ''
            string = string.replace(placeholder, replacement)

        return string

    @classmethod
    def _process_split_template(
            cls, elements, event_type, event_properties, event_attachments, colorize,
            ignore_value_errors, iteration_level=0
    ):
        result = ''

        for element in elements:
            if type(element) == list:
                processed = cls._process_split_template(
                    element, event_type, event_properties, event_attachments, colorize,
                    ignore_value_errors, iteration_level + 1
                )
            else:
                if element != '':
                    processed = cls._process_simple_placeholder_string(
                        event_type, element, event_properties, event_attachments, colorize, ignore_value_errors
                    )
                    if processed == '':
                        return ''
                else:
                    processed = ''

            result += processed

        return result

    @classmethod
    def _capitalize(cls, string):
        ansi_start = '\x1b[1m\x1b[37m'

        if string.startswith(ansi_start):
            return ansi_start + string[len(ansi_start)].capitalize() + string[len(ansi_start) + 1:]
        elif string == '':
            return string
        else:
            return string[0].capitalize() + string[1:]

    @classmethod
    def _get_placeholder_arguments(cls, placeholder):

        formatter, arguments = cls._parse_placeholder(placeholder)
        property_count = 1 if formatter is None else cls.FORMATTER_PROPERTY_COUNTS.get(formatter)

        if property_count is None:
            # Variable property count.
            if formatter == 'merge':
                if not arguments:
                    raise EDXMLOntologyValidationError(
                        'String formatter (%s) requires at least one property argument.' % formatter
                    )
                property_arguments = arguments
                other_arguments = []
            elif formatter == 'unless_empty':
                if len(arguments) < 2:
                    raise EDXMLOntologyValidationError(
                        'String formatter (%s) requires at least two arguments.' % formatter
                    )
                property_arguments = arguments[:-1]
                other_arguments = arguments[-1:]
            else:
                raise Exception('FORMATTER_PROPERTY_COUNTS is missing count for %s formatter.' % formatter)
        else:
            if len(arguments) < property_count:
                raise EDXMLOntologyValidationError(
                    'String formatter (%s) requires %d properties, only %d properties were specified.' %
                    (formatter, property_count, len(arguments))
                )
            property_arguments = arguments[:property_count]
            other_arguments = arguments[property_count:]

        return property_arguments, other_arguments

    @classmethod
    def _parse_placeholder(cls, placeholder):
        try:
            formatter, arguments = placeholder[2:-2].split(':', 1)
        except ValueError:
            # No placeholder present.
            formatter = None
            arguments = placeholder[2:-2]
        arguments = arguments.split(',')

        if arguments == ['']:
            # This is from a placeholder that looks like [[FORMATTER:]].
            # We regard that as a formatter without any arguments.
            arguments = []

        return formatter, arguments

    def get_property_names(self):
        """

        Returns a list containing all property names occurring
        in all placeholders in the template.

        Returns:
            List[str]: List of property names
        """
        properties = set()
        placeholders = re.findall(self.TEMPLATE_PATTERN, self._template)
        for placeholder in placeholders:
            property_arguments, _ = self._get_placeholder_arguments(placeholder)
            properties.update(property_arguments)
        return list(properties)
