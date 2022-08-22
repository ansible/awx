import { RRule, RRuleSet } from 'rrule';
import buildRuleObj, { buildDtStartObj } from './buildRuleObj';

window.RRuleSet = RRuleSet;

const frequencies = ['minute', 'hour', 'day', 'week', 'month', 'year'];
export default function buildRuleSet(values) {
  const set = new RRuleSet();

  const startRule = buildDtStartObj({
    startDate: values.startDate,
    startTime: values.startTime,
    timezone: values.timezone,
  });
  set.rrule(startRule);

  if (values.frequency.length === 0) {
    const rule = buildRuleObj({
      startDate: values.startDate,
      startTime: values.startTime,
      timezone: values.timezone,
      frequency: 'none',
      interval: 1,
    });
    set.rrule(new RRule(rule));
  }

  frequencies.forEach((frequency) => {
    if (!values.frequency.includes(frequency)) {
      return;
    }
    const rule = buildRuleObj({
      startDate: values.startDate,
      startTime: values.startTime,
      timezone: values.timezone,
      frequency,
      ...values.frequencyOptions[frequency],
    });
    set.rrule(new RRule(rule));
  });

  // TODO: exclusions

  return set;
}
