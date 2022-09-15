import { RRule } from 'rrule';
import buildRuleSet from './buildRuleSet';

import { DateTime } from 'luxon';

describe('buildRuleSet', () => {
  test('should build minutely recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=MINUTELY'
    );
  });

  test('should build hourly recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['hour'],
      frequencyOptions: {
        hour: {
          interval: 1,
          end: 'never',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=HOURLY'
    );
  });

  test('should build daily recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['day'],
      frequencyOptions: {
        day: {
          interval: 1,
          end: 'never',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=DAILY'
    );
  });

  test('should build weekly recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['week'],
      frequencyOptions: {
        week: {
          interval: 1,
          end: 'never',
          daysOfWeek: [RRule.SU],
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=SU'
    );
  });

  test('should build monthly by day recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['month'],
      frequencyOptions: {
        month: {
          interval: 1,
          end: 'never',
          runOn: 'day',
          runOnDayNumber: 15,
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=MONTHLY;BYMONTHDAY=15'
    );
  });

  test('should build monthly by weekday recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['month'],
      frequencyOptions: {
        month: {
          interval: 1,
          end: 'never',
          runOn: 'the',
          runOnTheOccurrence: 2,
          runOnTheDay: 'monday',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO'
    );
  });

  test('should build yearly by day recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['year'],
      frequencyOptions: {
        year: {
          interval: 1,
          end: 'never',
          runOn: 'day',
          runOnDayMonth: 3,
          runOnDayNumber: 15,
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=15'
    );
  });

  test('should build yearly by weekday recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['year'],
      frequencyOptions: {
        year: {
          interval: 1,
          end: 'never',
          runOn: 'the',
          runOnTheOccurrence: 4,
          runOnTheDay: 'monday',
          runOnTheMonth: 6,
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=4;BYDAY=MO;BYMONTH=6'
    );
  });

  test('should build combined frequencies', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute', 'month'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
        month: {
          interval: 1,
          end: 'never',
          runOn: 'the',
          runOnTheOccurrence: 2,
          runOnTheDay: 'monday',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(`DTSTART:20220613T123000Z
RRULE:INTERVAL=1;FREQ=MINUTELY
RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO`);
  });

  test('should build combined frequencies with end dates', () => {
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

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(`DTSTART;TZID=US/Eastern:20220601T123000
RRULE:INTERVAL=2;FREQ=HOURLY;UNTIL=20260702T170000Z
RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO;UNTIL=20260602T170000Z`);
  });

  test('should build single occurence', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: [],
      frequencyOptions: {},
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(`DTSTART:20220613T123000Z
RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY`);
  });

  test('should build minutely exception', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['minute'],
      exceptionOptions: {
        minute: {
          interval: 3,
          end: 'never',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=3;FREQ=MINUTELY',
      ].join('\n')
    );
  });

  test('should build hourly exception', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['hour'],
      exceptionOptions: {
        hour: {
          interval: 3,
          end: 'never',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=3;FREQ=HOURLY',
      ].join('\n')
    );
  });

  test('should build daily exception', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['day'],
      exceptionOptions: {
        day: {
          interval: 3,
          end: 'never',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=3;FREQ=DAILY',
      ].join('\n')
    );
  });

  test('should build weekly exception', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['week'],
      exceptionOptions: {
        week: {
          interval: 3,
          end: 'never',
          daysOfWeek: [RRule.SU],
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=3;FREQ=WEEKLY;BYDAY=SU',
      ].join('\n')
    );
  });

  test('should build monthly exception by day', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['month'],
      exceptionOptions: {
        month: {
          interval: 3,
          end: 'never',
          runOn: 'day',
          runOnDayNumber: 15,
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=3;FREQ=MONTHLY;BYMONTHDAY=15',
      ].join('\n')
    );
  });

  test('should build monthly exception by weekday', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['month'],
      exceptionOptions: {
        month: {
          interval: 3,
          end: 'never',
          runOn: 'the',
          runOnTheOccurrence: 2,
          runOnTheDay: 'monday',
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=3;FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO',
      ].join('\n')
    );
  });

  test('should build annual exception by day', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['year'],
      exceptionOptions: {
        year: {
          interval: 1,
          end: 'never',
          runOn: 'day',
          runOnDayMonth: 3,
          runOnDayNumber: 15,
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=1;FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=15',
      ].join('\n')
    );
  });

  test('should build annual exception by weekday', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute'],
      frequencyOptions: {
        minute: {
          interval: 1,
          end: 'never',
        },
      },
      exceptionFrequency: ['year'],
      exceptionOptions: {
        year: {
          interval: 1,
          end: 'never',
          runOn: 'the',
          runOnTheOccurrence: 4,
          runOnTheDay: 'monday',
          runOnTheMonth: 6,
        },
      },
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      [
        'DTSTART:20220613T123000Z',
        'RRULE:INTERVAL=1;FREQ=MINUTELY',
        'EXRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=4;BYDAY=MO;BYMONTH=6',
      ].join('\n')
    );
  });
});
