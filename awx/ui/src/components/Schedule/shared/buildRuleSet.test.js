import { RRule } from 'rrule';
import buildRuleSet from './buildRuleSet';

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
});
