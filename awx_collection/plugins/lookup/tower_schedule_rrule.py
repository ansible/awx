# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: tower_schedule_rrule
    author: John Westcott IV (@john-westcott-iv)
    version_added: "3.7"
    short_description: Generate an rrule string which can be used for Tower Schedules
    requirements:
      - pytz
      - python.dateutil
    description:
      - Returns a string based on criteria which represent an rule
    options:
      _terms:
        description:
          - The frequency of the schedule
          - none - Run this schedule once
          - minute - Run this schedule ever x minutes
          - hour - Run this schedule every x hours
          - day - Run this schedule ever x days
          - week - Run this schedule weekly
          - month - Run this schedule monthly
        required: True
        choices: ['none', 'minute', 'hour', 'day', 'week', 'month']
      start_date:
        description:
          - The date to start the rule
          - Used for all frequencies
          - Format should be YYYY-MM-DD [HH:MM:SS]
        type: str
      timezone:
        description:
          - The timezone to use for this rule
          - Used for all frequencies
          - Format should be as US/Eastern
          - Defaults to America/New_York
        type: str
      every:
        description:
          - The repition in months, weeks, days hours or minutes
          - Used for all types except none
        type: int
      end_on:
        description:
          - How to end this schedule
          - If this is not defined this schedule will never end
          - If this is a positive integer this schedule will end after this number of occurances
          - If this is a date in the format YYYY-MM-DD [HH:MM:SS] this schedule end after this date
          - Used for all types except none
        type: str
      on_days:
        description:
          - The days to run this schedule on
          - A comma seperated list which can contain values sunday, monday, tuesday, wednesday, thursday, friday
          - Used for week type schedules
      month_day_number:
        description:
          - The day of the month this schedule will run on (0-31)
          - Used for month type schedules
          - Can not be used with on_the parameter
        type: int
      on_the:
        description:
          - A description on when this schedule will run
          - Two strings seperated by space
          - First string is one of first, second, third, fourth, last
          - Second string is one of sunday, monday, tuesday, wednesday, thursday, friday
          - Used for month type schedules
          - Can not be used with month_day_number parameters
    extends_documentation_fragment: awx.awx.auth
"""

EXAMPLES = """
    - name: Create a string for a schedule
      debug:
        msg: "{{ query('awx.awx.tower_schedule_rrule', 'none', start_date='1979-09-13 03:45:07') }}"
"""

RETURN = """
_raw:
  description:
    - String in the rrule format
  type: string
"""

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from datetime import datetime
import re

missing_modules = []
try:
    import pytz
except ImportError:
    missing_modules.append('pytz')

try:
    from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, MO, TU, WE, TH, FR, SA, SU
except ImportError:
    missing_modules.append('python.dateutil')

if len(missing_modules) > 0:
    raise AnsibleError('You are missing the modules {0}'.format(', '.join(missing_modules)))

class LookupModule(LookupBase):
    frequencies = {
        'none': DAILY,
        'minute': MINUTELY,
        'hour': HOURLY,
        'day': DAILY,
        'week': WEEKLY,
        'month': MONTHLY,
    }

    weekdays = {
        'monday': MO,
        'tuesday': TU,
        'wednesday': WE,
        'thursday': TH,
        'friday': FR,
        'saturday': SA,
        'sunday': SU,
    }

    set_positions = {
        'first': 1,
        'second': 2,
        'third': 3,
        'fourth': 4,
        'last': -1,
    }

    def parse_date_time(self, date_string):
        try:
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.strptime(date_string, '%Y-%m-%d')

    def run(self, terms, variables=None, **kwargs):
        if len(terms) != 1:
            raise AnsibleError('You may only pass one schedule type in at a time')

        frequency = terms[0].lower()

        if frequency not in self.frequencies:
            raise AnsibleError('Frequency of {0} is invalid'.format(terms[0]))

        rrule_kwargs = {
            'freq': self.frequencies[frequency],
            'interval': kwargs.get('every', 1),
        }

        # All frequencies can use a start date
        if 'start_date' in kwargs:
            try:
                rrule_kwargs['dtstart'] = self.parse_date_time(kwargs['start_date'])
            except Exception:
                raise AnsibleError('Parameter start_date must be in the format YYYY-MM-DD [HH:MM:SS]')

        # If we are a none frequency we don't need anything else
        if frequency == 'none':
            rrule_kwargs['count'] = 1
        else:
            # All non-none frequencies can have an end_on option
            if 'end_on' in kwargs:
                end_on = kwargs['end_on']
                if re.match(r'^\d+$', end_on):
                    rrule_kwargs['count'] = end_on
                else:
                    try:
                        rrule_kwargs['until'] = self.parse_date_time(end_on)
                    except Exception:
                        raise AnsibleError('Parameter end_on must either be an integer or in the format YYYY-MM-DD [HH:MM:SS]')

            # A week based frequency can also take the on_days parameter
            if frequency == 'week' and 'on_days' in kwargs:
                days = []
                for day in kwargs['on_days'].split(','):
                    day = day.strip()
                    if day not in self.weekdays:
                        raise AnsibleError('Parameter on_days must only contain values {0}'.format(', '.join(self.weekdays.keys())))
                    days.append(self.weekdays[day])

                rrule_kwargs['byweekday'] = days

            # A month based frequency can also deal with month_day_number and on_the options
            if frequency == 'month':
                if 'month_day_number' in kwargs and 'on_the' in kwargs:
                    raise AnsibleError('Month based frquencies can have month_day_number or on_the but not both')

                if 'month_day_number' in kwargs:
                    try:
                        my_month_day = int(kwargs['month_day_number'])
                        if my_month_day < 1 or my_month_day > 31:
                            raise Exception()
                    except Exception:
                        raise AnsibleError('month_day_number must be between 1 and 31')

                    rrule_kwargs['bymonthday'] = my_month_day

                if 'on_the' in kwargs:
                    try:
                        (occurance, weekday) = kwargs['on_the'].split(' ')
                    except Exception:
                        raise AnsibleError('on_the parameter must be two space seperated words')

                    if weekday not in self.weekdays:
                        raise AnsibleError('Weekday portion of on_the parameter is not valid')
                    if occurance not in self.set_positions:
                        raise AnsibleError('The first string of the on_the parameter is not valid')

                    rrule_kwargs['byweekday'] = self.weekdays[weekday]
                    rrule_kwargs['bysetpos'] = self.set_positions[occurance]

        my_rule = rrule(**rrule_kwargs)

        # All frequencies can use a timezone but rrule can't support the format that tower uses.
        # So we will do a string manip here if we need to
        timezone = 'America/New_York'
        if 'timezone' in kwargs:
            if kwargs['timezone'] not in pytz.all_timezones:
                raise AnsibleError('Timezone parameter is not valid')
            timezone = kwargs['timezone']

        # rrule puts a \n in the rule instad of a space and can't hand timezones
        return_rrule = str(my_rule).replace('\n', ' ').replace('DTSTART:', 'DTSTART;TZID={0}:'.format(timezone))
        # Tower requires an interval. rrule will not add interval if its set to 1
        if kwargs.get('every', 1) == 1:
            return_rrule = "{0};INTERVAL=1".format(return_rrule)

        return return_rrule
