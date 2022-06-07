import { RRule } from 'rrule';
import { dateToInputDateTime } from 'util/dates';

export default function parseRuleObj(schedule) {
  const values = {};
  const {
    origOptions: {
      bymonth,
      bymonthday,
      bysetpos,
      byweekday,
      count,
      dtstart,
      freq,
      interval,
    },
  } = RRule.fromString(schedule.rrule.replace(' ', '\n'));

  if (dtstart) {
    const [startDate, startTime] = dateToInputDateTime(
      schedule.dtstart,
      schedule.timezone
    );

    values.startDate = startDate;
    values.startTime = startTime;
  }

  if (schedule.until) {
    values.end = 'onDate';

    const [endDate, endTime] = dateToInputDateTime(
      schedule.until,
      schedule.timezone
    );

    values.endDate = endDate;
    values.endTime = endTime;
  } else if (count) {
    values.end = 'after';
    values.occurrences = count;
  }

  if (interval) {
    values.interval = interval;
  }

  if (typeof freq === 'number') {
    switch (freq) {
      case RRule.MINUTELY:
        if (schedule.dtstart !== schedule.dtend) {
          values.frequency = 'minute';
        }
        break;
      case RRule.HOURLY:
        values.frequency = 'hour';
        break;
      case RRule.DAILY:
        values.frequency = 'day';
        break;
      case RRule.WEEKLY:
        values.frequency = 'week';
        if (byweekday) {
          values.daysOfWeek = byweekday;
        }
        break;
      case RRule.MONTHLY:
        values.frequency = 'month';
        if (bymonthday) {
          values.runOnDayNumber = bymonthday;
        } else if (bysetpos) {
          values.runOn = 'the';
          values.runOnTheOccurrence = bysetpos;
          values.runOnTheDay = generateRunOnTheDay(byweekday);
        }
        break;
      case RRule.YEARLY:
        values.frequency = 'year';
        if (bymonthday) {
          values.runOnDayNumber = bymonthday;
          values.runOnDayMonth = bymonth;
        } else if (bysetpos) {
          values.runOn = 'the';
          values.runOnTheOccurrence = bysetpos;
          values.runOnTheDay = generateRunOnTheDay(byweekday);
          values.runOnTheMonth = bymonth;
        }
        break;
      default:
        break;
    }
  }

  return values;
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
