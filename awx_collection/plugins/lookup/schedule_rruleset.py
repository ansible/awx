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
          every:
            description:
              - The repetition in months, weeks, days hours or minutes
              - Used for all types except none
            type: int
          end_on:
            description:
              - How to end this schedule
              - If this is not defined, this schedule will never end
              - If this is a positive integer, this schedule will end after this number of occurences
              - If this is a date in the format YYYY-MM-DD [HH:MM:SS], this schedule ends after this date
              - Used for all types except none
            type: str
          on_days:
            description:
              - The days to run this schedule on
              - A comma-separated list which can contain values sunday, monday, tuesday, wednesday, thursday, friday
              - Used for week type schedules
          month_day_number:
            description:
              - The day of the month this schedule will run on (0-31)
              - Used for month type schedules
              - Cannot be used with on_the parameter
            type: int
          on_the:
            description:
              - A description on when this schedule will run
              - Two strings separated by a space
              - First string is one of first, second, third, fourth, last
              - Second string is one of sunday, monday, tuesday, wednesday, thursday, friday
              - Used for month type schedules
              - Cannot be used with month_day_number parameters
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
            every: 1
          - frequency: 'day'
            every: 1
            on_days: 'sunday'
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
    LIBRARY_IMPORT_ERROR = imp_exc
else:
    LIBRARY_IMPORT_ERROR = None


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
        if LIBRARY_IMPORT_ERROR:
            raise_from(AnsibleError('{0}'.format(LIBRARY_IMPORT_ERROR)), LIBRARY_IMPORT_ERROR)
        super().__init__(*args, **kwargs)

    @staticmethod
    def parse_date_time(date_string):
        try:
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.strptime(date_string, '%Y-%m-%d')

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
            frequency = rule.get('frequency', None)
            if not frequency:
                raise AnsibleError("Rule {0} is missing a frequency".format(rule_number))
            if frequency not in LookupModule.frequencies:
                raise AnsibleError('Frequency of rule {0} is invalid {1}'.format(rule_number, frequency))

            rrule_kwargs = {
                'freq': LookupModule.frequencies[frequency],
                'interval': rule.get('every', 1),
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

                # A week-based frequency can also take the on_days parameter
                if 'on_days' in rule:
                    days = []
                    for day in rule['on_days'].split(','):
                        day = day.strip()
                        if day not in LookupModule.weekdays:
                            raise AnsibleError('In rule {0} on_days must only contain values {1}'.format(rule_number, ', '.join(LookupModule.weekdays.keys())))
                        days.append(LookupModule.weekdays[day])

                    rrule_kwargs['byweekday'] = days

                # A month-based frequency can also deal with month_day_number and on_the options
                if frequency == 'month':
                    if 'month_day_number' in rule and 'on_the' in rule:
                        raise AnsibleError('In rule {0} a month based frequencies can have month_day_number or on_the but not both'.format(rule_number))

                    if 'month_day_number' in rule:
                        try:
                            my_month_day = int(rule['month_day_number'])
                            if my_month_day < 1 or my_month_day > 31:
                                raise Exception()
                        except Exception as e:
                            raise_from(AnsibleError('In rule {0} month_day_number must be between 1 and 31'.format(rule_number)), e)

                        rrule_kwargs['bymonthday'] = my_month_day

                    if 'on_the' in rule:
                        try:
                            (occurance, weekday) = rule['on_the'].split(' ')
                        except Exception as e:
                            raise_from(AnsibleError('In rule {0} on_the parameter must be two words separated by a space'.format(rule_number)), e)

                        if weekday not in LookupModule.weekdays:
                            raise AnsibleError('In rule {0} weekday portion of on_the parameter is not valid'.format(rule_number))
                        if occurance not in LookupModule.set_positions:
                            raise AnsibleError('In rule {0} the first string of the on_the parameter is not valid'.format(rule_number))

                        rrule_kwargs['byweekday'] = LookupModule.weekdays[weekday]
                        rrule_kwargs['bysetpos'] = LookupModule.set_positions[occurance]

            generated_rule = str(rrule.rrule(**rrule_kwargs))

            # AWX requires an interval. rrule will not add interval if it's set to 1
            if rule.get('every', 1) == 1:
                generated_rule = "{0};INTERVAL=1".format(generated_rule)

            if rule_index == 0:
                # rrule puts a \n in the rule instad of a space and can't handle timezones
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
            raise_from("Failed to parse generated rule set via rruleset", e)

        # return self.get_rrule(frequency, kwargs)
        return rruleset_str
