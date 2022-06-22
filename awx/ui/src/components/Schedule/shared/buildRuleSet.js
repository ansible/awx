import { RRule, RRuleSet } from 'rrule';
import buildRuleObj from './buildRuleObj';

const frequencies = ['minute', 'hour', 'day', 'week', 'month', 'year'];
export default function buildRuleSet(values) {
  const set = new RRuleSet();

  frequencies.forEach((freq) => {
    if (!values.frequency.includes(freq)) {
      return;
    }
    const prefix = `frequency_${freq}`;

    const rule = buildRuleObj({
      startDate: values.startDate,
      startTime: values.startTime,
      timezone: values.timezone,
      frequency: freq,
      interval: values[`${prefix}_interval`],
      daysOfWeek: values[`${prefix}_daysOfWeek`],
      runOn: values[`${prefix}_runOn`],
      runOnTheDay: values[`${prefix}_runOnTheDay`],
      runOnTheMonth: values[`${prefix}_runOnTheMonth`],
      runOnDayMonth: values[`${prefix}_runOnDayMonth`],
      runOnDayNumber: values[`${prefix}_runOnDayNumber`],
      runOnTheOccurrence: values[`${prefix}_runOnTheOccurrence`],
      occurences: values[`${prefix}_occurences`],
      end: values[`${prefix}_end`],
    });
    set.rrule(new RRule(rule));

    // TODO: exclusions
  });

  return set;
}
