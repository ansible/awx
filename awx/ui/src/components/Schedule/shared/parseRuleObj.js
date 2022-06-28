import { RRule, rrulestr } from 'rrule';
import { dateToInputDateTime } from 'util/dates';
import sortFrequencies from './sortFrequencies';

export default function parseRuleObj(schedule) {
  let values = {
    frequency: [],
    frequencyOptions: {},
    exceptionFrequency: [],
    exceptionOptions: {},
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
      default:
        throw new Error(`Unsupported rrule type: ${type}`);
    }
  });

  return values;
}

function parseDtstart(schedule, values) {
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
  const {
    origOptions: {
      bymonth,
      bymonthday,
      bysetpos,
      byweekday,
      count,
      freq,
      interval,
    },
  } = RRule.fromString(rruleString);

  const options = {};

  if (schedule.until) {
    options.end = 'onDate';

    // options.endDate = ?;
    // options.endTime = ?;
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
  if (values.frequency.includes(frequency)) {
    throw new Error(`Duplicate frequency types not supported (${frequency})`);
  }

  if (frequency === RRule.WEEKLY && byweekday) {
    options.daysOfWeek = byweekday;
  }
  if (frequency === RRule.MONTHLY && bymonthday) {
    options.runOnDayNumber = bymonthday;
  }
  if (frequency === RRule.MONTHLY && bysetpos) {
    options.runOn = 'the';
    options.runOnTheOccurrence = bysetpos;
    options.runOnTheDay = generateRunOnTheDay(byweekday);
  }
  if (frequency === RRule.YEARLY && bymonthday) {
    options.runOnDayNumber = bymonthday;
    options.runOnDayMonth = bymonth;
  }
  if (frequency === RRule.YEARLY && bysetpos) {
    options.runOn = 'the';
    options.runOnTheOccurrence = bysetpos;
    options.runOnTheDay = generateRunOnTheDay(byweekday);
    options.runOnTheMonth = bymonth;
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
