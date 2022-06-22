import { RRule } from 'rrule';
import buildRuleSet from './buildRuleSet';

describe('buildRuleSet', () => {
  test('should build minutely recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      interval: 1,
      frequency: ['minute'],
      frequency_minute_end: 'never',
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=MINUTELY'
    );
  });

  test('should build hourly recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      interval: 1,
      frequency: ['hour'],
      frequency_hour_end: 'never',
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=HOURLY'
    );
  });

  test('should build daily recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      interval: 1,
      frequency: ['day'],
      frequency_day_end: 'never',
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=DAILY'
    );
  });

  test('should build weekly recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      interval: 1,
      frequency: ['week'],
      frequency_week_end: 'never',
      frequency_week_daysOfWeek: [RRule.SU],
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=WEEKLY;BYDAY=SU'
    );
  });

  test('should build monthly by day recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['month'],
      interval: 1,
      frequency_month_end: 'never',
      frequency_month_runOn: 'day',
      frequency_month_runOnDayNumber: 15,
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=MONTHLY;BYMONTHDAY=15'
    );
  });

  test('should build monthly by weekday recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['month'],
      interval: 1,
      frequency_minute_end: 'never',
      frequency_month_end: 'never',
      frequency_month_runOn: 'the',
      frequency_month_runOnTheOccurrence: 2,
      frequency_month_runOnTheDay: 'monday',
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO'
    );
  });

  test('should build yearly by day recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['year'],
      interval: 1,
      frequency_year_end: 'never',
      frequency_year_runOn: 'day',
      frequency_year_runOnDayMonth: 3,
      frequency_year_runOnDayNumber: 15,
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=15'
    );
  });

  test('should build yearly by weekday recurring rrule', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['year'],
      interval: 1,
      frequency_year_end: 'never',
      frequency_year_runOn: 'the',
      frequency_year_runOnTheOccurrence: 4,
      frequency_year_runOnTheDay: 'monday',
      frequency_year_runOnTheMonth: 6,
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(
      'DTSTART:20220613T123000Z\nRRULE:FREQ=YEARLY;BYSETPOS=4;BYDAY=MO;BYMONTH=6'
    );
  });

  test('should build combined frequencies', () => {
    const values = {
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['minute', 'month'],
      interval: 1,
      frequency_minute_end: 'never',
      frequency_month_end: 'never',
      frequency_month_runOn: 'the',
      frequency_month_runOnTheOccurrence: 2,
      frequency_month_runOnTheDay: 'monday',
    };

    const ruleSet = buildRuleSet(values);
    expect(ruleSet.toString()).toEqual(`DTSTART:20220613T123000Z
RRULE:FREQ=MINUTELY
DTSTART:20220613T123000Z
RRULE:FREQ=MONTHLY;BYSETPOS=2;BYDAY=MO`);
  });
});
