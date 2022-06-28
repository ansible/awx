import { RRule, RRuleSet } from 'rrule';
import buildRuleObj from './buildRuleObj';

const frequencies = ['minute', 'hour', 'day', 'week', 'month', 'year'];
export default function buildRuleSet(values) {
  const set = new RRuleSet();

  frequencies.forEach((frequency) => {
    if (!values.frequency.includes(frequency)) {
      return;
    }
    const rule = buildRuleObj({
      startDate: values.startDate,
      startTime: values.startTime,
      startInfo: values.timezone,
      frequency,
      ...values.frequencyOptions[frequency],
    });
    set.rrule(new RRule(rule));

    // TODO: exclusions
  });

  return set;
}
