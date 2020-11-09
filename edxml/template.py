import re
from typing import Dict

import edxml.ontology

from dateutil import relativedelta
from dateutil.parser import parse
from edxml.error import EDXMLValidationError
from iso3166 import countries
from termcolor import colored


class Template(object):

    TEMPLATE_PATTERN = re.compile('\\[\\[([^\\]]*)\\]\\]')
    KNOWN_FORMATTERS = (
        'TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
        'CURRENCY', 'COUNTRYCODE', 'MERGE',
        'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY', 'NEWPAR', 'URL'
    )

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

        zero_argument_formatters = ['COUNTRYCODE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']

        if property_names is None:
            properties = event_type.get_properties()
        else:
            properties = {(name, prop) for name, prop in event_type.get_properties().items() if name in property_names}

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

        for template in placeholder_strings:
            # TODO: Write one generic check for existing properties by creating a table of
            # formatters, mapping formatter names to the indexes into the argument list of
            # arguments that are property names.
            try:
                formatter, argument_string = str(template).split(':', 1)
                arguments = argument_string.split(',')
            except ValueError:
                # Placeholder does not contain a formatter.
                if str(template) in properties.keys():
                    continue
                else:
                    raise EDXMLValidationError(
                        'Template refers to one or more properties that either do not exist or '
                        'that must not be used in this template.'
                    )

            # Some kind of string formatter was used.
            # Figure out which one, and check if it
            # is used correctly.
            if formatter in ['DURATION', 'TIMESPAN']:

                if len(arguments) != 2:
                    raise EDXMLValidationError(
                        'String formatter (%s) requires two properties, but %d properties were specified.' %
                        (formatter, len(arguments))
                    )

                if arguments[0] in properties.keys() and arguments[1] in properties.keys():

                    # Check that both properties are datetime values
                    for property_name in arguments:
                        if property_name == '':
                            raise EDXMLValidationError(
                                'Invalid property name in %s formatter: "%s"' % (property_name, formatter)
                            )
                        if str(properties[property_name].get_data_type()) != 'datetime':
                            raise EDXMLValidationError(
                                 'Time related formatter (%s) used on property (%s) which is not a datetime value.' % (
                                    formatter, property_name
                                 )
                            )

                    continue
            else:
                if formatter not in self.KNOWN_FORMATTERS:
                    raise EDXMLValidationError('Unknown formatter: %s' % formatter)

                if formatter in ['DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR']:
                    # Check that only one property is specified after the formatter
                    if len(arguments) > 1:
                        raise EDXMLValidationError(
                            'The %s formatter accepts just one property, multiple properties were specified: %s' % (
                                formatter, argument_string
                            )
                        )
                    # Check that property is a datetime value
                    if argument_string == '':
                        raise EDXMLValidationError(
                            'Invalid property name in %s formatter: "%s"' % (argument_string, formatter)
                        )
                    if str(properties[argument_string].get_data_type()) != 'datetime':
                        raise EDXMLValidationError(
                            'The %s formatter was used on property %s which is not a datetime value' % (
                                formatter, argument_string
                            )
                        )

                elif formatter in zero_argument_formatters:
                    # Check that no additional arguments are present
                    if len(arguments) > 1:
                        raise EDXMLValidationError(
                            'The %s formatter accepts no arguments, but they were specified: %s' % (
                                formatter, template
                            )
                        )
                    # Check that only one property is specified after the formatter
                    if len(arguments) > 1:
                        raise EDXMLValidationError(
                            'The %s formatter accepts just one property. Multiple properties were given: %s' % (
                                formatter, argument_string
                            )
                        )
                    if formatter in ['BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
                        # Check that property is a boolean
                        if argument_string == '':
                            raise EDXMLValidationError(
                                'Invalid property name in %s formatter: "%s"' % (argument_string, formatter)
                            )
                        if str(properties[argument_string].get_data_type()) != 'boolean':
                            raise EDXMLValidationError(
                                'The %s formatter was used on property %s which is not a boolean.' % (
                                    formatter, argument_string
                                )
                            )

                elif formatter == 'CURRENCY':
                    if len(arguments) != 2:
                        raise EDXMLValidationError(
                            'Malformed %s formatter: %s' % (formatter, template)
                        )

                elif formatter == 'URL':
                    if len(arguments) != 2:
                        raise EDXMLValidationError(
                            'Malformed %s formatter: %s' % (formatter, template)
                        )

                elif formatter == 'EMPTY':
                    if len(arguments) != 2:
                        raise EDXMLValidationError(
                            'Malformed %s formatter: %s' % (formatter, template)
                        )

                elif formatter == 'NEWPAR':
                    if len(arguments) != 1 or arguments[0] != '':
                        raise EDXMLValidationError(
                            'Malformed %s formatter: %s' % (formatter, template)
                        )

                elif formatter == 'BOOLEAN_STRINGCHOICE':
                    if len(arguments) != 3:
                        raise EDXMLValidationError(
                            'Malformed %s formatter: %s' % (formatter, template)
                        )
                    # Check that property is a boolean
                    if argument_string == '':
                        raise EDXMLValidationError(
                            'Invalid property name in %s formatter: "%s"' % (argument_string, formatter)
                        )
                    if str(properties[arguments[0]].get_data_type()) != 'boolean':
                        raise EDXMLValidationError(
                            'The %s formatter was used on property %s which is not a boolean.' % (
                                formatter, argument_string
                            )
                        )

                elif formatter == 'MERGE':
                    # No special requirements to check for
                    pass

                else:
                    raise EDXMLValidationError('Unknown formatter: "%s"' % formatter)

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
    def _format_time_duration(time_min, time_max):
        date_time_a = parse(time_min)
        date_time_b = parse(time_max)
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
        placeholders = re.findall(r'(\[\[([^]]*)\]\])', string)

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

            if not formatter:
                try:
                    object_strings.extend(event_object_values[arguments[0]])
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

            elif formatter == 'TIMESPAN':

                date_time_strings = []
                for property_name in arguments:
                    try:
                        for object_value in event_object_values[property_name]:
                            date_time_strings.append(object_value)
                    except KeyError:
                        pass

                if len(date_time_strings) > 0:
                    # Note that we use lexicographic sorting here.
                    date_time_a = parse(min(date_time_strings))
                    date_time_b = parse(max(date_time_strings))
                    object_strings.append('between %s and %s' % (
                        date_time_a.isoformat(' '), date_time_b.isoformat(' ')))
                else:
                    # No valid replacement string could be generated, which implies
                    # that we must return an empty string.
                    return ''

            elif formatter == 'DURATION':

                date_time_strings = []
                for property_name in arguments:
                    try:
                        for object_value in event_object_values[property_name]:
                            date_time_strings.append(object_value)
                    except KeyError:
                        pass

                if len(date_time_strings) > 0:
                    object_strings.append(cls._format_time_duration(
                        min(date_time_strings), max(date_time_strings)))
                else:
                    # No valid replacement string could be generated, which implies
                    # that we must return an empty string.
                    return ''

            elif formatter in ['YEAR', 'MONTH', 'WEEK', 'DATE', 'DATETIME', 'FULLDATETIME']:

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                for object_value in values:
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

            elif formatter == 'CURRENCY':

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                property_name, currency_symbol = arguments
                for object_value in values:
                    object_strings.append('%.2f%s' % (int(object_value), currency_symbol))

            elif formatter == 'URL':

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                property_name, target_name = arguments
                for object_value in values:
                    object_strings.append('%s (%s)' % (target_name, object_value))

            elif formatter == 'MERGE':

                for property_name in arguments:
                    try:
                        for object_value in event_object_values[property_name]:
                            object_strings.append(object_value)
                    except KeyError:
                        pass

            elif formatter == 'COUNTRYCODE':

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                for object_value in values:
                    try:
                        object_strings.append(
                            countries.get(object_value).name)
                    except KeyError:
                        object_strings.append(object_value + ' (unknown country code)')

            elif formatter == 'BOOLEAN_STRINGCHOICE':

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                property_name, true, false = arguments
                for object_value in values:
                    if object_value == 'true':
                        object_strings.append(true)
                    else:
                        object_strings.append(false)

            elif formatter == 'BOOLEAN_ON_OFF':

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                for object_value in values:
                    if object_value == 'true':
                        # Print 'on'
                        object_strings.append('on')
                    else:
                        # Print 'off'
                        object_strings.append('off')

            elif formatter == 'BOOLEAN_IS_ISNOT':

                try:
                    values = event_object_values[arguments[0]]
                except KeyError:
                    # Property has no object, which implies that
                    # we must produce an empty result.
                    return ''

                for object_value in values:
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
                    object_strings.append(arguments[0])
                else:
                    # Property has an object, so the formatter will
                    # yield an empty string. This in turn implies that
                    # we must produce an empty result.
                    return ''

            elif formatter == 'NEWPAR':

                object_strings.append('\n')

            else:

                # String has no associated formatter but maybe the the data
                # type implies an appropriate value format.
                property_name = arguments[0]
                if property_data_types[property_name].type == 'geo:point':
                    try:
                        values = event_object_values[property_name]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        lat, long = object_value.split(',')
                        degrees = int(lat)
                        minutes = int((lat - degrees) * 60.0)
                        seconds = int((lat - degrees - (minutes / 60.0)) * 3600.0)

                        lat_long = '%d°%d′%d %s″' % (degrees, minutes, seconds, 'N' if degrees > 0 else 'S')

                        degrees = int(long)
                        minutes = int((long - degrees) * 60.0)
                        seconds = int((long - degrees - (minutes / 60.0)) * 3600.0)

                        lat_long += ' %d°%d′%d %s″' % (degrees, minutes, seconds, 'E' if degrees > 0 else 'W')

                        object_strings.append(lat_long)

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
                    element, event_properties, event_type, capitalize, colorize, iteration_level + 1
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
