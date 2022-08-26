import { DateTime, Settings } from 'luxon';
import { RRule } from 'rrule';
import parseRuleObj from './parseRuleObj';
import buildRuleSet from './buildRuleSet';

describe(parseRuleObj, () => {
  let origNow = Settings.now;
  beforeEach(() => {
    const expectedNow = DateTime.local(2022, 6, 1, 13, 0, 0);
    Settings.now = () => expectedNow.toMillis();
  });

  afterEach(() => {
    Settings.now = origNow;
  });

  test('should parse weekly recurring rrule', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=US/Eastern:20220608T123000 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=MO',
      dtstart: '2022-06-13T16:30:00Z',
      timezone: 'US/Eastern',
      until: '',
      dtend: null,
    };

    const parsed = parseRuleObj(schedule);

    expect(parsed).toEqual({
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      timezone: 'US/Eastern',
      frequency: ['week'],
      frequencyOptions: {
        week: {
          interval: 1,
          end: 'never',
          occurrences: 1,
          endDate: '2022-06-02',
          endTime: '1:00 PM',
          daysOfWeek: [RRule.MO],
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });

  test('should parse weekly recurring rrule with end date', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20210101T050000Z',
      dtstart: '2020-04-02T18:45:00Z',
      timezone: 'America/New_York',
    };

    const parsed = parseRuleObj(schedule);

    expect(parsed).toEqual({
      startDate: '2020-04-02',
      startTime: '2:45 PM',
      timezone: 'America/New_York',
      frequency: ['week'],
      frequencyOptions: {
        week: {
          interval: 1,
          end: 'onDate',
          occurrences: 1,
          endDate: '2021-01-01',
          endTime: '12:00 AM',
          daysOfWeek: [RRule.MO, RRule.WE, RRule.FR],
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });

  test('should parse hourly rule with end date', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=US/Eastern:20220608T123000 RRULE:INTERVAL=1;FREQ=HOURLY;UNTIL=20230608T170000Z',
      dtstart: '2022-06-08T16:30:00Z',
      timezone: 'US/Eastern',
    };

    const parsed = parseRuleObj(schedule);

    expect(parsed).toEqual({
      startDate: '2022-06-08',
      startTime: '12:30 PM',
      timezone: 'US/Eastern',
      frequency: ['hour'],
      frequencyOptions: {
        hour: {
          interval: 1,
          end: 'onDate',
          occurrences: 1,
          endDate: '2023-06-08',
          endTime: '1:00 PM',
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });

  // TODO: do we need to support this? It's technically invalid RRULE, but the
  // API has historically supported it as a special case (but cast to UTC?)
  test.skip('should parse hourly rule with end date in local time', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=US/Eastern:20220608T123000 RRULE:INTERVAL=1;FREQ=HOURLY;UNTIL=20230608T130000',
      dtstart: '2022-06-08T16:30:00',
      timezone: 'US/Eastern',
    };

    const parsed = parseRuleObj(schedule);

    expect(parsed).toEqual({
      startDate: '2022-06-08',
      startTime: '12:30 PM',
      timezone: 'US/Eastern',
      frequency: ['hour'],
      frequencyOptions: {
        hour: {
          interval: 1,
          end: 'onDate',
          occurrences: 1,
          endDate: '2023-06-08',
          endTime: '1:00 PM',
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });

  test('should parse non-recurring rrule', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=America/New_York:20220610T130000 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
      dtstart: '2022-06-10T17:00:00Z',
      dtend: '2022-06-10T17:00:00Z',
      timezone: 'US/Eastern',
      until: '',
    };

    expect(parseRuleObj(schedule)).toEqual({
      startDate: '2022-06-10',
      startTime: '1:00 PM',
      timezone: 'US/Eastern',
      frequency: [],
      frequencyOptions: {},
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });

  // buildRuleSet is well-tested; use it to verify this does the inverse
  test('should re-parse built complex schedule', () => {
    const values = {
      startDate: '2022-06-01',
      startTime: '12:30 PM',
      timezone: 'US/Eastern',
      frequency: ['minute', 'month'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
          endDate: '2022-06-02',
          endTime: '1:00 PM',
          occurrences: 1,
        },
        month: {
          interval: 1,
          end: 'never',
          runOn: 'the',
          runOnTheOccurrence: 2,
          runOnTheDay: 'monday',
          runOnDayNumber: 1,
          endDate: '2022-06-02',
          endTime: '1:00 PM',
          occurrences: 1,
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    };

    const ruleSet = buildRuleSet(values);
    const parsed = parseRuleObj({
      rrule: ruleSet.toString(),
      dtstart: '2022-06-01T12:30:00',
      dtend: '2022-06-01T12:30:00',
      timezone: 'US/Eastern',
    });

    expect(parsed).toEqual(values);
  });

  test('should parse built complex schedule with end dates', () => {
    const rulesetString = `DTSTART;TZID=US/Eastern:20220601T123000
RRULE:INTERVAL=2;FREQ=HOURLY;UNTIL=20260702T170000Z
RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO;UNTIL=20260602T170000Z`;
    const values = {
      startDate: '2022-06-01',
      startTime: '12:30 PM',
      timezone: 'US/Eastern',
      frequency: ['hour', 'month'],
      frequencyOptions: {
        hour: {
          interval: 2,
          end: 'onDate',
          endDate: '2026-07-02',
          endTime: '1:00 PM',
          occurrences: 1,
        },
        month: {
          interval: 1,
          end: 'onDate',
          runOn: 'the',
          runOnTheOccurrence: 2,
          runOnTheDay: 'monday',
          runOnDayNumber: 1,
          endDate: '2026-06-02',
          endTime: '1:00 PM',
          occurrences: 1,
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    };

    const parsed = parseRuleObj({
      rrule: rulesetString,
      dtstart: '2022-06-01T16:30:00Z',
      dtend: '2026-06-07T16:30:00Z',
      timezone: 'US/Eastern',
    });

    expect(parsed).toEqual(values);
  });

  test('should parse exemptions', () => {
    const schedule = {
      rrule: [
        'DTSTART;TZID=US/Eastern:20220608T123000',
        'RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=MO',
        'EXRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=1;BYDAY=MO',
      ].join(' '),
      dtstart: '2022-06-13T16:30:00Z',
      timezone: 'US/Eastern',
      until: '',
      dtend: null,
    };

    const parsed = parseRuleObj(schedule);

    expect(parsed).toEqual({
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      timezone: 'US/Eastern',
      frequency: ['week'],
      frequencyOptions: {
        week: {
          interval: 1,
          end: 'never',
          occurrences: 1,
          endDate: '2022-06-02',
          endTime: '1:00 PM',
          daysOfWeek: [RRule.MO],
        },
      },
      exceptionFrequency: ['month'],
      exceptionOptions: {
        month: {
          interval: 1,
          end: 'never',
          endDate: '2022-06-02',
          endTime: '1:00 PM',
          occurrences: 1,
          runOn: 'the',
          runOnDayNumber: 1,
          runOnTheOccurrence: 1,
          runOnTheDay: 'monday',
        },
      },
    });
  });
});
