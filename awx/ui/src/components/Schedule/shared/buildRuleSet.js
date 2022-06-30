import { RRule, RRuleSet } from 'rrule';
import buildRuleObj from './buildRuleObj';

const frequencies = ['minute', 'hour', 'day', 'week', 'month', 'year'];
export default function buildRuleSet(values) {
  const set = new RRuleSet();

  if (values.frequency.length === 0) {
    const rule = buildRuleObj(
      {
        startDate: values.startDate,
        startTime: values.startTime,
        timezone: values.timezone,
        frequency: 'none',
        interval: 1,
      },
      true
    );
    set.rrule(new RRule(rule));
  }

  let isFirst = true;
  frequencies.forEach((frequency) => {
    if (!values.frequency.includes(frequency)) {
      return;
    }
    const rule = buildRuleObj(
      {
        startDate: values.startDate,
        startTime: values.startTime,
        timezone: values.timezone,
        frequency,
        ...values.frequencyOptions[frequency],
      },
      isFirst
    );
    set.rrule(new RRule(rule));

    isFirst = false;

    // TODO: exclusions
  });

  return set;
}
