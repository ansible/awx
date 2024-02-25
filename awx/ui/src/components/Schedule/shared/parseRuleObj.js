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
    frequency: [],
    frequencyOptions: {},
    exceptionFrequency: [],
    exceptionOptions: {},
    timezone: schedule.timezone,
  };
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

  if (isSingleOccurrence(values)) {
    values.frequency = [];
    values.frequencyOptions = {};
  }

  return values;
}

function isSingleOccurrence(values) {
  if (values.frequency.length > 1) {
    return false;
  }
  if (values.frequency[0] !== 'minute') {
    return false;
  }
  const options = values.frequencyOptions.minute;
  return options.end === 'after' && options.occurrences === 1;
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

function parseRrule(rruleString, schedule, values) {
  const { frequency, options } = parseRule(rruleString, schedule);

  if (values.frequencyOptions[frequency]) {
    throw new UnsupportedRRuleError(
      'Duplicate exception frequency types not supported'
    );
  }

  return {
    ...values,
    frequency: [...values.frequency, frequency].sort(sortFrequencies),
    frequencyOptions: {
      ...values.frequencyOptions,
      [frequency]: options,
    },
  };
}

function parseExRule(exruleString, schedule, values) {
  const { frequency, options } = parseRule(exruleString, schedule);

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
    origOptions: {
      bymonth,
      bymonthday,
      bysetpos,
      byweekday,
      count,
      freq,
      interval,
      until,
    },
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
    end: 'never',
  };

  if (until) {
    options.end = 'onDate';
    const end = DateTime.fromISO(until.toISOString());
    const [endDate, endTime] = dateToInputDateTime(end, schedule.timezone);
    options.endDate = endDate;
    options.endTime = endTime;
  } else if (count) {
    options.end = 'after';
    options.occurrences = count;
  }

  if (interval) {
    options.interval = interval;
  }

  if (typeof freq !== 'number') {
    throw new Error(`Unexpected rrule frequency: ${freq}`);
  }
  const frequency = frequencyTypes[freq];

  if (freq === RRule.WEEKLY && byweekday) {
    options.daysOfWeek = byweekday;
  }

  if (freq === RRule.MONTHLY) {
    options.runOn = 'day';
    options.runOnTheOccurrence = 1;
    options.runOnTheDay = 'sunday';
    options.runOnDayNumber = 1;

    if (bymonthday) {
      options.runOnDayNumber = bymonthday;
    }
    if (bysetpos) {
      options.runOn = 'the';
      options.runOnTheOccurrence = bysetpos;
      options.runOnTheDay = generateRunOnTheDay(byweekday);
    }
  }

  if (freq === RRule.YEARLY) {
    options.runOn = 'day';
    options.runOnTheOccurrence = 1;
    options.runOnTheDay = 'sunday';
    options.runOnTheMonth = 1;
    options.runOnDayMonth = 1;
    options.runOnDayNumber = 1;

    if (bymonthday) {
      options.runOnDayNumber = bymonthday;
      options.runOnDayMonth = bymonth;
    }
    if (bysetpos) {
      options.runOn = 'the';
      options.runOnTheOccurrence = bysetpos;
      options.runOnTheDay = generateRunOnTheDay(byweekday);
      options.runOnTheMonth = bymonth;
    }
  }

  return {
    frequency,
    options,
  };
}

function generateRunOnTheDay(days = []) {
  if (
    [
      RRule.MO,
      RRule.TU,
      RRule.WE,
      RRule.TH,
      RRule.FR,
      RRule.SA,
      RRule.SU,
    ].every((element) => days.indexOf(element) > -1)
  ) {
    return 'day';
  }
  if (
    [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR].every(
      (element) => days.indexOf(element) > -1
    )
  ) {
    return 'weekday';
  }
  if ([RRule.SA, RRule.SU].every((element) => days.indexOf(element) > -1)) {
    return 'weekendDay';
  }
  if (days.indexOf(RRule.MO) > -1) {
    return 'monday';
  }
  if (days.indexOf(RRule.TU) > -1) {
    return 'tuesday';
  }
  if (days.indexOf(RRule.WE) > -1) {
    return 'wednesday';
  }
  if (days.indexOf(RRule.TH) > -1) {
    return 'thursday';
  }
  if (days.indexOf(RRule.FR) > -1) {
    return 'friday';
  }
  if (days.indexOf(RRule.SA) > -1) {
    return 'saturday';
  }
  if (days.indexOf(RRule.SU) > -1) {
    return 'sunday';
  }

  return null;
}
