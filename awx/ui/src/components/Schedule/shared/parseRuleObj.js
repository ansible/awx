import { RRule, rrulestr } from 'rrule';
import { dateToInputDateTime } from 'util/dates';
import { DateTime } from 'luxon';
import sortFrequencies from './sortFrequencies';

export class UnsupportedRRuleError extends Error {
  constructor(message) {
    super(message);
    this.name = 'UnsupportedRRuleError';
  }
}

export default function parseRuleObj(schedule) {
  let values = {
    frequency: '',
    rrules: '',
    timezone: schedule.timezone,
  };
  if (Object.values(schedule).length === 0) {
    return values;
  }

  const ruleset = rrulestr(schedule.rrule.replace(' ', '\n'), {
    forceset: true,
  });

  const ruleStrings = ruleset.valueOf();
  ruleStrings.forEach((ruleString) => {
    const type = ruleString.match(/^[A-Z]+/)[0];
    switch (type) {
      case 'DTSTART':
        values = parseDtstart(schedule, values);
        break;
      case 'RRULE':
        values = parseRrule(ruleString, schedule, values);
        break;
      case 'EXRULE':
        values = parseExRule(ruleString, schedule, values);
        break;
      default:
        throw new UnsupportedRRuleError(`Unsupported rrule type: ${type}`);
    }
  });

  return values;
}

function parseDtstart(schedule, values) {
  // TODO: should this rely on DTSTART in rruleset rather than schedule.dtstart?
  const [startDate, startTime] = dateToInputDateTime(
    schedule.dtstart,
    schedule.timezone
  );
  return {
    ...values,
    startDate,
    startTime,
  };
}

const frequencyTypes = {
  [RRule.MINUTELY]: 'minute',
  [RRule.HOURLY]: 'hour',
  [RRule.DAILY]: 'day',
  [RRule.WEEKLY]: 'week',
  [RRule.MONTHLY]: 'month',
  [RRule.YEARLY]: 'year',
};

function parseRrule(rruleString, schedule) {
  const { frequency } = parseRule(rruleString, schedule);

  const freq = { frequency, rrule: rruleString };

  return freq;
}

function parseExRule(exruleString, schedule, values) {
  const { frequency, options } = parseRule(
    exruleString,
    schedule,
    values.exceptionFrequency
  );

  if (values.exceptionOptions[frequency]) {
    throw new UnsupportedRRuleError(
      'Duplicate exception frequency types not supported'
    );
  }

  return {
    ...values,
    exceptionFrequency: [...values.exceptionFrequency, frequency].sort(
      sortFrequencies
    ),
    exceptionOptions: {
      ...values.exceptionOptions,
      [frequency]: options,
    },
  };
}

function parseRule(ruleString, schedule) {
  const {
    origOptions: { count, freq, interval, until, ...rest },
  } = RRule.fromString(ruleString);
  const now = DateTime.now();
  const closestQuarterHour = DateTime.fromMillis(
    Math.ceil(now.ts / 900000) * 900000
  );
  const tomorrow = closestQuarterHour.plus({ days: 1 });
  const [, time] = dateToInputDateTime(closestQuarterHour.toISO());
  const [tomorrowDate] = dateToInputDateTime(tomorrow.toISO());

  const options = {
    endDate: tomorrowDate,
    endTime: time,
    occurrences: 1,
    interval: 1,
    endingType: 'never',
  };

  if (until?.length) {
    options.endingType = 'onDate';
    const end = DateTime.fromISO(until.toISOString());
    const [endDate, endTime] = dateToInputDateTime(end, schedule.timezone);
    options.endDate = endDate;
    options.endTime = endTime;
  } else if (count) {
    options.endingType = 'after';
    options.occurrences = count;
  }

  if (interval) {
    options.interval = interval;
  }

  if (typeof freq !== 'number') {
    throw new Error(`Unexpected rrule frequency: ${freq}`);
  }
  const frequency = frequencyTypes[freq];

  return {
    frequency,
    ...options,
    ...rest,
  };
}
