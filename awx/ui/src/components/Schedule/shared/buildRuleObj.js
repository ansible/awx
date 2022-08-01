import { t } from '@lingui/macro';
import { RRule } from 'rrule';
import { DateTime } from 'luxon';
import { getRRuleDayConstants } from 'util/dates';

const parseTime = (time) => [
  DateTime.fromFormat(time, 'h:mm a').hour,
  DateTime.fromFormat(time, 'h:mm a').minute,
];

export default function buildRuleObj(values, includeStart) {
  const ruleObj = {
    interval: values.interval,
    tzid: values.timezone,
  };

  if (includeStart) {
    // Dates are formatted like "YYYY-MM-DD"
    const [startYear, startMonth, startDay] = values.startDate.split('-');
    // Times are formatted like "HH:MM:SS" or "HH:MM" if no seconds
    // have been specified
    const [startHour, startMinute] = parseTime(values.startTime);
    ruleObj.dtstart = new Date(
      Date.UTC(
        startYear,
        parseInt(startMonth, 10) - 1,
        startDay,
        startHour,
        startMinute
      )
    );
  }

  switch (values.frequency) {
    case 'none':
      ruleObj.count = 1;
      ruleObj.freq = RRule.MINUTELY;
      break;
    case 'minute':
      ruleObj.freq = RRule.MINUTELY;
      break;
    case 'hour':
      ruleObj.freq = RRule.HOURLY;
      break;
    case 'day':
      ruleObj.freq = RRule.DAILY;
      break;
    case 'week':
      ruleObj.freq = RRule.WEEKLY;
      ruleObj.byweekday = values.daysOfWeek;
      break;
    case 'month':
      ruleObj.freq = RRule.MONTHLY;
      if (values.runOn === 'day') {
        ruleObj.bymonthday = values.runOnDayNumber;
      } else if (values.runOn === 'the') {
        ruleObj.bysetpos = parseInt(values.runOnTheOccurrence, 10);
        ruleObj.byweekday = getRRuleDayConstants(values.runOnTheDay);
      }
      break;
    case 'year':
      ruleObj.freq = RRule.YEARLY;
      if (values.runOn === 'day') {
        ruleObj.bymonth = parseInt(values.runOnDayMonth, 10);
        ruleObj.bymonthday = values.runOnDayNumber;
      } else if (values.runOn === 'the') {
        ruleObj.bysetpos = parseInt(values.runOnTheOccurrence, 10);
        ruleObj.byweekday = getRRuleDayConstants(values.runOnTheDay);
        ruleObj.bymonth = parseInt(values.runOnTheMonth, 10);
      }
      break;
    default:
      throw new Error(t`Frequency did not match an expected value`);
  }

  if (values.frequency !== 'none') {
    switch (values.end) {
      case 'never':
        break;
      case 'after':
        ruleObj.count = values.occurrences;
        break;
      case 'onDate': {
        const [endHour, endMinute] = parseTime(values.endTime);
        const localEndDate = DateTime.fromISO(`${values.endDate}T000000`);
        const localEndTime = localEndDate.set({
          hour: endHour,
          minute: endMinute,
          second: 0,
        });
        const utcEndTime = localEndTime.setZone('UTC');
        ruleObj.until = utcEndTime.toJSDate();

        // const [endYear, endMonth, endDay] = values.endDate.split('-');

        // const [endHour, endMinute] = parseTime(values.endTime);
        // ruleObj.until = new Date(
        //   Date.UTC(
        //     endYear,
        //     parseInt(endMonth, 10) - 1,
        //     endDay,
        //     endHour,
        //     endMinute
        //   )
        // );
        break;
      }
      default:
        throw new Error(t`End did not match an expected value`);
    }
  }

  return ruleObj;
}
