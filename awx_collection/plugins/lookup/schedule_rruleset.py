# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
    lookup: schedule_rruleset
    author: John Westcott IV (@john-westcott-iv)
    short_description: Generate an rruleset string
    requirements:
      - pytz
      - python-dateutil >= 2.7.0
    description:
      - Returns a string based on criteria which represents an rrule
    options:
      _terms:
        description:
          - The start date of the ruleset
          - Used for all frequencies
          - Format should be YYYY-MM-DD [HH:MM:SS]
        required: True
        type: str
      timezone:
        description:
          - The timezone to use for this rule
          - Used for all frequencies
          - Format should be as US/Eastern
          - Defaults to America/New_York
        type: str
      rules:
        description:
          - Array of rules in the rruleset
        type: array
        required: True
        suboptions:
          frequency:
            description:
              - The frequency of the schedule
              - none - Run this schedule once
              - minute - Run this schedule every x minutes
              - hour - Run this schedule every x hours
              - day - Run this schedule every x days
              - week - Run this schedule weekly
              - month - Run this schedule monthly
            required: True
            choices: ['none', 'minute', 'hour', 'day', 'week', 'month']
          interval:
            description:
              - The repetition in months, weeks, days hours or minutes
              - Used for all types except none
            type: int
          end_on:
            description:
              - How to end this schedule
              - If this is not defined, this schedule will never end
              - If this is a positive integer, this schedule will end after this number of occurrences
              - If this is a date in the format YYYY-MM-DD [HH:MM:SS], this schedule ends after this date
              - Used for all types except none
            type: str
          bysetpos:
            description:
              - Specify an occurrence number, corresponding to the nth occurrence of the rule inside the frequency period.
              - A comma-separated list of positions (first, second, third, forth or last)
            type: string
          bymonth:
            description:
              - The months this schedule will run on
              - A comma-separated list which can contain values 0-12
            type: string
          bymonthday:
            description:
              - The day of the month this schedule will run on
              - A comma-separated list which can contain values 0-31
            type: string
          byyearday:
            description:
              - The year day numbers to run this schedule on
              - A comma-separated list which can contain values 0-366
            type: string
          byweekno:
            description:
              - The week numbers to run this schedule on
              - A comma-separated list which can contain values as described in ISO8601
            type: string
          byweekday:
            description:
              - The days to run this schedule on
              - A comma-separated list which can contain values sunday, monday, tuesday, wednesday, thursday, friday
            type: string
          byhour:
            description:
              - The hours to run this schedule on
              - A comma-separated list which can contain values 0-23
            type: string
          byminute:
            description:
              - The minutes to run this schedule on
              - A comma-separated list which can contain values 0-59
            type: string
          include:
            description:
              - If this rule should be included (RRULE) or excluded (EXRULE)
            type: bool
            default: True
"""

EXAMPLES = """
    - name: Create a ruleset for everyday except Sundays
      set_fact:
        complex_rule: "{{ query(awx.awx.schedule_rruleset, '2022-04-30 10:30:45', rules=rrules, timezone='UTC' ) }}"
      vars:
        rrules:
          - frequency: 'day'
            interval: 1
          - frequency: 'day'
            interval: 1
            byweekday: 'sunday'
            include: False
"""

RETURN = """
_raw:
  description:
    - String in the rrule format
  type: string
"""
import re

from ansible.module_utils.six import raise_from
from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from datetime import datetime

try:
    import pytz
    from dateutil import rrule
except ImportError as imp_exc:
    raise_from(AnsibleError('{0}'.format(imp_exc)), imp_exc)


class LookupModule(LookupBase):
    frequencies = {
        'none': rrule.DAILY,
        'minute': rrule.MINUTELY,
        'hour': rrule.HOURLY,
        'day': rrule.DAILY,
        'week': rrule.WEEKLY,
        'month': rrule.MONTHLY,
    }

    weekdays = {
        'monday': rrule.MO,
        'tuesday': rrule.TU,
        'wednesday': rrule.WE,
        'thursday': rrule.TH,
        'friday': rrule.FR,
        'saturday': rrule.SA,
        'sunday': rrule.SU,
    }

    set_positions = {
        'first': 1,
        'second': 2,
        'third': 3,
        'fourth': 4,
        'last': -1,
    }

    # plugin constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def parse_date_time(date_string):
        try:
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.strptime(date_string, '%Y-%m-%d')

    def process_integer(self, field_name, rule, min_value, max_value, rule_number):
        # We are going to tolerate multiple types of input here:
        # something: 1 - A single integer
        # something: "1" - A single str
        # something: "1,2,3" - A comma separated string of ints
        # something: "1, 2,3" - A comma separated string of ints (with spaces)
        # something: ["1", "2", "3"] - A list of strings
        # something: [1,2,3] - A list of ints
        return_values = []
        # If they give us a single int, lets make it a list of ints
        if type(rule[field_name]) == int:
            rule[field_name] = [rule[field_name]]
        # If its not a list, we need to split it into a list
        if type(rule[field_name]) != list:
            rule[field_name] = rule[field_name].split(',')
        for value in rule[field_name]:
            # If they have a list of strs we want to strip the str incase its space delineated
            if type(value) == str:
                value = value.strip()
            # If value happens to be an int (from a list of ints) we need to coerce it into a str for the re.match
            if not re.match(r"^\d+$", str(value)) or int(value) < min_value or int(value) > max_value:
                raise AnsibleError('In rule {0} {1} must be between {2} and {3}'.format(rule_number, field_name, min_value, max_value))
            return_values.append(int(value))
        return return_values

    def process_list(self, field_name, rule, valid_list, rule_number):
        return_values = []
        if type(rule[field_name]) != list:
            rule[field_name] = rule[field_name].split(',')
        for value in rule[field_name]:
            value = value.strip()
            if value not in valid_list:
                raise AnsibleError('In rule {0} {1} must only contain values in {2}'.format(rule_number, field_name, ', '.join(valid_list.keys())))
            return_values.append(valid_list[value])
        return return_values

    def run(self, terms, variables=None, **kwargs):
        if len(terms) != 1:
            raise AnsibleError('You may only pass one schedule type in at a time')

        # Validate the start date
        try:
            start_date = LookupModule.parse_date_time(terms[0])
        except Exception as e:
            raise_from(AnsibleError('The start date must be in the format YYYY-MM-DD [HH:MM:SS]'), e)

        if not kwargs.get('rules', None):
            raise AnsibleError('You must include rules to be in the ruleset via the rules parameter')

        # All frequencies can use a timezone but rrule can't support the format that AWX uses.
        # So we will do a string manip here if we need to
        timezone = 'America/New_York'
        if 'timezone' in kwargs:
            if kwargs['timezone'] not in pytz.all_timezones:
                raise AnsibleError('Timezone parameter is not valid')
            timezone = kwargs['timezone']

        rules = []
        got_at_least_one_rule = False
        for rule_index in range(0, len(kwargs['rules'])):
            rule = kwargs['rules'][rule_index]
            rule_number = rule_index + 1
            valid_options = [
                "frequency",
                "interval",
                "end_on",
                "bysetpos",
                "bymonth",
                "bymonthday",
                "byyearday",
                "byweekno",
                "byweekday",
                "byhour",
                "byminute",
                "include",
            ]
            invalid_options = list(set(rule.keys()) - set(valid_options))
            if invalid_options:
                raise AnsibleError('Rule {0} has invalid options: {1}'.format(rule_number, ', '.join(invalid_options)))
            frequency = rule.get('frequency', None)
            if not frequency:
                raise AnsibleError("Rule {0} is missing a frequency".format(rule_number))
            if frequency not in LookupModule.frequencies:
                raise AnsibleError('Frequency of rule {0} is invalid {1}'.format(rule_number, frequency))

            rrule_kwargs = {
                'freq': LookupModule.frequencies[frequency],
                'interval': rule.get('interval', 1),
                'dtstart': start_date,
            }

            # If we are a none frequency we don't need anything else
            if frequency == 'none':
                rrule_kwargs['count'] = 1
            else:
                # All non-none frequencies can have an end_on option
                if 'end_on' in rule:
                    end_on = rule['end_on']
                    if re.match(r'^\d+$', end_on):
                        rrule_kwargs['count'] = end_on
                    else:
                        try:
                            rrule_kwargs['until'] = LookupModule.parse_date_time(end_on)
                        except Exception as e:
                            raise_from(
                                AnsibleError('In rule {0} end_on must either be an integer or in the format YYYY-MM-DD [HH:MM:SS]'.format(rule_number)), e
                            )

            if 'bysetpos' in rule:
                rrule_kwargs['bysetpos'] = self.process_list('bysetpos', rule, LookupModule.set_positions, rule_number)

            if 'bymonth' in rule:
                rrule_kwargs['bymonth'] = self.process_integer('bymonth', rule, 1, 12, rule_number)

            if 'bymonthday' in rule:
                rrule_kwargs['bymonthday'] = self.process_integer('bymonthday', rule, 1, 31, rule_number)

            if 'byyearday' in rule:
                rrule_kwargs['byyearday'] = self.process_integer('byyearday', rule, 1, 366, rule_number)  # 366 for leap years

            if 'byweekno' in rule:
                rrule_kwargs['byweekno'] = self.process_integer('byweekno', rule, 1, 52, rule_number)

            if 'byweekday' in rule:
                rrule_kwargs['byweekday'] = self.process_list('byweekday', rule, LookupModule.weekdays, rule_number)

            if 'byhour' in rule:
                rrule_kwargs['byhour'] = self.process_integer('byhour', rule, 0, 23, rule_number)

            if 'byminute' in rule:
                rrule_kwargs['byminute'] = self.process_integer('byminute', rule, 0, 59, rule_number)

            try:
                generated_rule = str(rrule.rrule(**rrule_kwargs))
            except Exception as e:
                raise_from(AnsibleError('Failed to parse rrule for rule {0} {1}: {2}'.format(rule_number, str(rrule_kwargs), e)), e)

            # AWX requires an interval. rrule will not add interval if it's set to 1
            if rule.get('interval', 1) == 1:
                generated_rule = "{0};INTERVAL=1".format(generated_rule)

            if rule_index == 0:
                # rrule puts a \n in the rule instead of a space and can't handle timezones
                generated_rule = generated_rule.replace('\n', ' ').replace('DTSTART:', 'DTSTART;TZID={0}:'.format(timezone))
            else:
                # Only the first rule needs the dtstart in a ruleset so remaining rules we can split at \n
                generated_rule = generated_rule.split('\n')[1]

            # If we are an exclude rule we need to flip from an rrule to an ex rule
            if not rule.get('include', True):
                generated_rule = generated_rule.replace('RRULE', 'EXRULE')
            else:
                got_at_least_one_rule = True

            rules.append(generated_rule)

        if not got_at_least_one_rule:
            raise AnsibleError("A ruleset must contain at least one RRULE")

        rruleset_str = ' '.join(rules)

        # For a sanity check lets make sure our rule can parse. Not sure how we can test this though
        try:
            rules = rrule.rrulestr(rruleset_str)
        except Exception as e:
            raise_from(AnsibleError("Failed to parse generated rule set via rruleset {0}".format(e)), e)

        # return self.get_rrule(frequency, kwargs)
        return rruleset_str
