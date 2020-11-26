import re
from typing import Dict

import edxml.ontology

from dateutil import relativedelta
from dateutil.parser import parse
from edxml.error import EDXMLValidationError
from iso3166 import countries
from termcolor import colored


class Template(object):

    TEMPLATE_PATTERN = re.compile(r'\[\[([^]]*)]]')

    KNOWN_FORMATTERS = (
        'TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
        'COUNTRYCODE', 'MERGE',
        'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY', 'NEWPAR', 'URL'
    )

    DATE_TIME_FORMATTERS = ['TIMESPAN', 'DURATION', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR']

    BOOLEAN_FORMATTERS = ['BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']

    FORMATTER_PROPERTY_COUNTS = {
        'TIMESPAN': 2,
        'DATE': 1,
        'DATETIME': 1,
        'FULLDATETIME': 1,
        'WEEK': 1,
        'MONTH': 1,
        'YEAR': 1,
        'DURATION': 2,
        'COUNTRYCODE': 1,
        'BOOLEAN_STRINGCHOICE': 1,
        'BOOLEAN_ON_OFF': 1,
        'BOOLEAN_IS_ISNOT': 1,
        'EMPTY': 1,
        'NEWPAR': 0,
        'URL': 1
    }

    FORMATTER_ARGUMENT_COUNTS = {
        'TIMESPAN': 2,
        'DATE': 1,
        'DATETIME': 1,
        'FULLDATETIME': 1,
        'WEEK': 1,
        'MONTH': 1,
        'YEAR': 1,
        'DURATION': 2,
        'COUNTRYCODE': 1,
        'BOOLEAN_STRINGCHOICE': 3,
        'BOOLEAN_ON_OFF': 1,
        'BOOLEAN_IS_ISNOT': 1,
        'EMPTY': 1,
        'NEWPAR': 0,
        'URL': 2
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
          EDXMLValidationError

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
                raise EDXMLValidationError('Unbalanced curly brackets')
        if nesting != 0:
            raise EDXMLValidationError('Unbalanced curly brackets')

        placeholder_strings = re.findall(self.TEMPLATE_PATTERN, self._template)

        for placeholder in placeholder_strings:
            try:
                formatter, argument_string = str(placeholder).split(':', 1)
                arguments = argument_string.split(',')
            except ValueError:
                # Placeholder does not contain a formatter. We only need to
                # check if the placeholder is a valid property name and skip
                # to the next placeholder.
                if placeholder not in properties.keys():
                    raise EDXMLValidationError(
                        'Template refers to a property named "%s" which either do not exist or '
                        'which cannot be used in this template.' % placeholder
                    )
                continue

            if formatter not in self.KNOWN_FORMATTERS:
                raise EDXMLValidationError('Unknown formatter: %s' % formatter)

            property_count = self.FORMATTER_PROPERTY_COUNTS.get(formatter)

            if property_count is None:
                # Variable property count.
                if formatter == 'MERGE':
                    property_arguments = arguments
                    other_arguments = []
                else:
                    raise Exception('FORMATTER_PROPERTY_COUNTS is missing count for %s formatter.' % formatter)
            else:
                if len(arguments) < property_count:
                    raise EDXMLValidationError(
                        'String formatter (%s) requires %d properties, only %d properties were specified.' %
                        (formatter, property_count, len(arguments))
                    )
                property_arguments = arguments[:property_count]
                other_arguments = arguments[property_count:]

            for property_name in property_arguments:
                if property_name == '':
                    raise EDXMLValidationError(
                        'Empty property name in %s formatter.' % formatter
                    )
                if property_name not in properties.keys():
                    raise EDXMLValidationError(
                        'Template refers to a property named "%s" which either do not exist or '
                        'which cannot be used in this template.' % property_name
                    )

            argument_count = self.FORMATTER_ARGUMENT_COUNTS.get(formatter)

            if argument_count is not None and len(property_arguments) + len(other_arguments) != argument_count:
                raise EDXMLValidationError(
                    'The %s formatter accepts %d arguments, but %d were specified: %s' % (
                        formatter, argument_count, len(property_arguments) + len(other_arguments), placeholder
                    )
                )

            if formatter in self.DATE_TIME_FORMATTERS:
                # Check that both properties are datetime values
                for property_name in property_arguments:
                    if str(properties[property_name].get_data_type()) != 'datetime':
                        raise EDXMLValidationError(
                             'Time related formatter (%s) used on property (%s) which is not a datetime value.' % (
                                formatter, property_name
                             )
                        )

            if formatter in self.BOOLEAN_FORMATTERS:
                # Check that property is a boolean
                for property_name in property_arguments:
                    if str(properties[property_name].get_data_type()) != 'boolean':
                        raise EDXMLValidationError(
                            'The %s formatter was used on property %s which is not a boolean.' % (
                                formatter, property_name
                            )
                        )

        return self

    def evaluate(self, event_type, edxml_event, capitalize=True, colorize=False):
        """

        Evaluates the EDXML template of an event type using
        specified event, returning the result.

        By default, we will try to capitalize the first letter of the resulting
        string, unless capitalize is set to False.

        Optionally, the output can be colorized. At his time this means that,
        when printed on the terminal, the objects in the evaluated string will
        be displayed using bold white characters.

        Args:
          event_type (edxml.ontology.EventType): the event type of the event
          edxml_event (edxml.EDXMLEvent): the EDXML event to use
          capitalize (bool): Capitalize output or not
          colorize (bool): Colorize output or not

        Returns:
          str:
        """

        return self._process_split_template(
            self._split_template(self._template)[1], event_type, edxml_event.get_properties(), capitalize, colorize
        )

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
    def _process_simple_placeholder_string(cls, event_type, string, event_object_values, capitalize_string, colorize):
        """

        Args:
            event_type (edxml.ontology.EventType):
            string (str):
            event_object_values (Dict[str, set]):
            capitalize_string (bool):
            colorize (bool):

        Returns:
            str
        """

        replacements = {}

        if capitalize_string and string != '':
            if string[0] == '{':
                if string[1:2] != '[[':
                    # Sting does not start with a placeholder,
                    # so we can safely capitalize.
                    string = string[0] + string[1].upper() + string[2:]
            else:
                if string[0:1] != '[[':
                    # Sting does not start with a placeholder,
                    # so we can safely capitalize.
                    string = string[0].upper() + string[1:]

        # Match on placeholders like "[[FULLDATETIME:datetime]]", creating
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
                    event_object_values[property_name] = {'%f' % float(value) for value in values}

        for placeholder in placeholders:

            object_strings = []
            try:
                formatter, argument_string = placeholder[1].split(':', 1)
                arguments = argument_string.split(',')
            except ValueError:
                # No formatter present.
                formatter = None
                arguments = placeholder[1].split(',')

            if formatter == 'TIMESPAN':

                try:
                    # Note that we use lexicographic sorting here.
                    date_time_start = parse(min(event_object_values[arguments[0]]))
                    date_time_end = parse(min(event_object_values[arguments[1]]))
                except ValueError:
                    # An argument was missing or a property is missing an object
                    # value. This implies that we must return an empty string.
                    return ''

                object_strings.append(
                    'between %s and %s' % (date_time_start.isoformat(' '), date_time_end.isoformat(' '))
                )

            elif formatter == 'DURATION':

                try:
                    # Note that we use lexicographic sorting here.
                    date_time_start = parse(min(event_object_values[arguments[0]]))
                    date_time_end = parse(min(event_object_values[arguments[1]]))
                except ValueError:
                    # An argument was missing or a property is missing an object
                    # value. This implies that we must return an empty string.
                    return ''

                object_strings.append(
                    cls._format_time_duration(date_time_start, date_time_end)
                )

            elif formatter in ['YEAR', 'MONTH', 'WEEK', 'DATE', 'DATETIME', 'FULLDATETIME']:

                for object_value in event_object_values[arguments[0]]:
                    date_time = parse(object_value)

                    try:
                        if formatter == 'FULLDATETIME':
                            object_strings.append(date_time.strftime('%A, %B %d %Y at %H:%M:%Sh UTC'))
                        elif formatter == 'DATETIME':
                            object_strings.append(date_time.strftime('%B %d %Y at %H:%M:%Sh UTC'))
                        elif formatter == 'DATE':
                            object_strings.append(date_time.strftime('%a, %B %d %Y'))
                        elif formatter == 'YEAR':
                            object_strings.append(date_time.strftime('%Y'))
                        elif formatter == 'MONTH':
                            object_strings.append(date_time.strftime('%B %Y'))
                        elif formatter == 'WEEK':
                            object_strings.append(date_time.strftime('week %W of %Y'))
                    except ValueError:
                        # This may happen for some time stamps before year 1900, which
                        # is not supported by strftime.
                        object_strings.append('some date, a long, long time ago')

            elif formatter == 'URL':

                property_name, target_name = arguments
                for object_value in event_object_values[arguments[0]]:
                    object_strings.append('%s (%s)' % (target_name, object_value))

            elif formatter == 'MERGE':

                for property_name in arguments:
                    for object_value in event_object_values[property_name]:
                        object_strings.append(object_value)

            elif formatter == 'COUNTRYCODE':

                for object_value in event_object_values[arguments[0]]:
                    try:
                        object_strings.append(countries.get(object_value).name)
                    except KeyError:
                        object_strings.append(object_value + ' (unknown country code)')

            elif formatter == 'BOOLEAN_STRINGCHOICE':

                property_name, true, false = arguments
                for object_value in event_object_values[arguments[0]]:
                    if object_value == 'true':
                        object_strings.append(true)
                    else:
                        object_strings.append(false)

            elif formatter == 'BOOLEAN_ON_OFF':

                for object_value in event_object_values[arguments[0]]:
                    if object_value == 'true':
                        # Print 'on'
                        object_strings.append('on')
                    else:
                        # Print 'off'
                        object_strings.append('off')

            elif formatter == 'BOOLEAN_IS_ISNOT':

                for object_value in event_object_values[arguments[0]]:
                    if object_value == 'true':
                        # Print 'is'
                        object_strings.append('is')
                    else:
                        # Print 'is not'
                        object_strings.append('is not')

            elif formatter == 'EMPTY':

                property_name = arguments[0]
                if property_name not in event_object_values or len(event_object_values[property_name]) == 0:
                    # Property has no object, use the second formatter argument
                    # in stead of the object value itself.
                    object_strings.append(arguments[1])

            elif formatter == 'NEWPAR':

                object_strings.append('\n')

            else:

                # String has no associated formatter but maybe the the data
                # type implies an appropriate value format.
                property_name = arguments[0]
                if property_name in property_data_types and property_data_types[property_name].type == 'geo:point':
                    for object_value in event_object_values[property_name]:
                        lat, long = object_value.split(',')
                        degrees = int(float(lat))
                        minutes = int((float(lat) - degrees) * 60.0)
                        seconds = int((float(lat) - degrees - (minutes / 60.0)) * 3600.0)

                        lat_long = '%d°%d′%d %s″' % (degrees, minutes, seconds, 'N' if degrees > 0 else 'S')

                        degrees = int(float(long))
                        minutes = int((float(long) - degrees) * 60.0)
                        seconds = int((float(long) - degrees - (minutes / 60.0)) * 3600.0)

                        lat_long += ' %d°%d′%d %s″' % (degrees, minutes, seconds, 'E' if degrees > 0 else 'W')

                        object_strings.append(lat_long)
                else:
                    object_strings.extend(event_object_values[property_name])

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
    def _process_split_template(cls, elements, event_type, event_properties, capitalize, colorize, iteration_level=0):
        result = ''

        for element in elements:
            if type(element) == list:
                processed = cls._process_split_template(
                    element, event_type, event_properties, capitalize, colorize, iteration_level + 1
                )
                capitalize = False
            else:
                if element != '':
                    processed = cls._process_simple_placeholder_string(
                        event_type, element, event_properties, capitalize, colorize
                    )
                    capitalize = False
                else:
                    processed = ''
            result += processed

        return result
