import { RRule, RRuleSet } from 'rrule';
import buildRuleObj, { buildDtStartObj } from './buildRuleObj';
import { FREQUENCIESCONSTANTS } from './scheduleFormHelpers';

window.RRuleSet = RRuleSet;

const frequencies = ['minute', 'hour', 'day', 'week', 'month', 'year'];
export default function buildRuleSet(values, useUTCStart) {
  const set = new RRuleSet();

  if (!useUTCStart) {
    const startRule = buildDtStartObj({
      startDate: values.startDate,
      startTime: values.startTime,
      timezone: values.timezone,
      frequency: values.freq,
    });
    set.rrule(startRule);
  }

  values.frequencies.forEach(({ frequency, rrule }) => {
    if (!frequencies.includes(frequency)) {
      return;
    }

    const rule = buildRuleObj(
      {
        startDate: values.startDate,
        startTime: values.startTime,
        timezone: values.timezone,
        freq: FREQUENCIESCONSTANTS[frequency],
        rrule,
      },
      true
    );

    set.rrule(new RRule(rule));
  });

  values.exceptions?.forEach(({ frequency, rrule }) => {
    if (!values.exceptionFrequency?.includes(frequency)) {
      return;
    }
    const rule = buildRuleObj(
      {
        startDate: values.startDate,
        startTime: values.startTime,
        timezone: values.timezone,
        freq: FREQUENCIESCONSTANTS[frequency],
        rrule,
      },
      useUTCStart
    );
    set.exrule(new RRule(rule));
  });

  return set;
}
