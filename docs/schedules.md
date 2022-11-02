## Scheduled Jobs

AWX allows jobs to run on a schedule (with optional recurrence rules) via
an `HTTP POST` to a variety of API endpoints:

    HTTP POST

    https://tower-host.example.org/api/v2/job_templates/N/schedules/
    https://tower-host.example.org/api/v2/projects/N/schedules/
    https://tower-host.example.org/api/v2/inventory_sources/N/schedules/
    https://tower-host.example.org/api/v2/system_jobs/N/schedules/
    https://tower-host.example.org/api/v2/workflow_job_templates/N/schedules/

    {
        'name': 'My Schedule Name',
        'rrule': 'DTSTART:20300115T120000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=7'
        'extra_data': {}
    }

...where `rrule` is a valid
[RFC5545](https://www.rfc-editor.org/rfc/rfc5545.txt) RRULE string and within AWX [RRULE Limitations](#rrule-limitations).
The specific example above would run a job every day - for seven consecutive days - starting
on January 15th, 2030 at noon (UTC).

For more examples see [RRULE Examples](#rrule-examples).

## Specifying Timezones

`DTSTART` values provided to AWX _must_ provide timezone information (they may
not be naive dates).

For UTC dates, `DTSTART` values should be denoted with the `Z` suffix:

    DTSTART:20300115T120000Z

Local timezones can be specified using the `TZID=` parameter:

    DTSTART;TZID=America/New_York:20300115T120000

A list of _valid_ zone identifiers (which can vary by system) can be found at:

    HTTP GET /api/v2/schedules/zoneinfo/

    [
        {"name": "Africa/Abidjan"},
        {"name": "Africa/Accra"},
        {"name": "Africa/Addis_Ababa"},
        ...
    ]


## UNTIL and Timezones

`DTSTART` values provided to AWX _must_ provide timezone information (they may
not be naive dates).

Additionally, RFC5545 specifies that:

> Furthermore, if the "DTSTART" property is specified as a date with local
> time, then the UNTIL rule part MUST also be specified as a date with local
> time.  If the "DTSTART" property is specified as a date with UTC time or
> a date with local time and time zone reference, then the UNTIL rule part
> MUST be specified as a date with UTC time.

Given this, `RRULE` values that specify `UNTIL` datetimes must *always* be in UTC.

Valid:
    `DTSTART:20180601T120000Z RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20180606T170000Z`
    `DTSTART;TZID=America/New_York:20180601T120000 RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20180606T170000Z`

Not Valid:

    `DTSTART:20180601T120000Z RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20180606T170000`
    `DTSTART;TZID=America/New_York:20180601T120000 RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20180606T170000`


## Previewing Schedules

AWX provides an endpoint for previewing the future dates and times for
a specified `RRULE`.  A list of the next _ten_ occurrences will be returned in
local and UTC time:

    POST https://tower-host.example.org/api/v2/schedules/preview/
    {
        'rrule': 'DTSTART;TZID=America/New_York:20300115T120000 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=7'
    }

    Content-Type: application/json
    {
        "local": [
            "2030-01-15T12:00:00-05:00",
            "2030-01-16T12:00:00-05:00",
            "2030-01-17T12:00:00-05:00",
            "2030-01-18T12:00:00-05:00",
            "2030-01-19T12:00:00-05:00",
            "2030-01-20T12:00:00-05:00",
            "2030-01-21T12:00:00-05:00"
        ],
        "utc": [
            "2030-01-15T17:00:00Z",
            "2030-01-16T17:00:00Z",
            "2030-01-17T17:00:00Z",
            "2030-01-18T17:00:00Z",
            "2030-01-19T17:00:00Z",
            "2030-01-20T17:00:00Z",
            "2030-01-21T17:00:00Z"
        ]
    }


## RRULE Limitations

AWX implements the following constraints on top of the `RFC5545` specification:

* The RRULE must start with the `DTSTART` attribute
* At least one `RRULE` entry must be in the rrule
* Strings with more than a single `DTSTART:` component are prohibited
* The use of `RDATE` or `EXDATE`is prohibited
* For any of the rules in the rrule:
    * `Interval` must be included
    * The use of `FREQ=SECONDLY` is prohibited
    * The usage of a `BYDAY` with a prefixed number is prohibited
    * The usage of both `COUNT` and `UNTIL` in the same rule is prohibited
    * The use of `COUNT=` with a value over 999 is prohibited

## Implementation Details

Any time an `awx.model.Schedule` is saved with a valid `rrule` value, the
`dateutil` library is used to burst out a list of all occurrences.  From here,
the following dates are saved in the database:

* `main_schedule.rrule` - the original `RRULE` string provided by the user
* `main_schedule.dtstart` - the _first_ datetime in the list of all occurrences (coerced to UTC)
* `main_schedule.dtend` - the _last_ datetime in the list of all occurrences (coerced to UTC)
* `main_schedule.next_run` - the _next_ datetime in list after `utcnow()` (coerced to UTC)

AWX makes use of [Celery Periodic Tasks
(celerybeat)](http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html)
to run a periodic task that discovers new jobs that need to run at a regular
interval (by default, every 30 seconds).  When this task starts, it queries the
database for Schedules where `Schedule.next_run` is between
`scheduler_last_runtime()` and `utcnow()`.  For each of these, a new job is
launched, and `Schedule.next_run` is changed to the next chronological datetime
in the list of all occurences.


## Complex RRULE Examples

Every day except for April 30th:

    DTSTART;TZID=US/Eastern:20230428T170000 RRULE:INTERVAL=1;FREQ=DAILY EXRULE:INTERVAL=1;FREQ=DAILY;BYMONTH=4;BYMONTHDAY=30

Every 5 minutes but not on Mondays from 5-7pm:

    DTSTART;TZID=America/New_York:20220418T164500 RRULE:INTERVAL=5;FREQ=MINUTELY EXRULE:FREQ=MINUTELY;INTERVAL=5;BYDAY=MO;BYHOUR=17,18

Every 15 minutes Monday to Friday from 10:01am to 6:02pm (inclusive):

    DTSTART;TZID=America/New_York:20220417T100100 RRULE:INTERVAL=15;FREQ=MINUTELY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=10,11,12,13,14,15,16,17,18 EXRULE:INTERVAL=15;FREQ=MINUTELY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=18;BYMINUTE=3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,34,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59

Any Saturday whose month day is between 12 and 18:

    DTSTART:20191219T130551Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=SA;BYMONTHDAY=12,13,14,15,16,17,18


