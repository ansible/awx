import { RRule } from 'rrule';
import { DateTime } from 'luxon';

window.RRule = RRule;
window.DateTime = DateTime;

const parseTime = (time) => [
  DateTime.fromFormat(time, 'h:mm a').hour,
  DateTime.fromFormat(time, 'h:mm a').minute,
];

export function buildDtStartObj(values) {
  // Dates are formatted like "YYYY-MM-DD"
  const [startYear, startMonth, startDay] = values.startDate.split('-');
  // Times are formatted like "HH:MM:SS" or "HH:MM" if no seconds
  // have been specified
  const [startHour, startMinute] = parseTime(values.startTime);

  const dateString = `${startYear}${pad(startMonth)}${pad(startDay)}T${pad(
    startHour
  )}${pad(startMinute)}00`;
  const rruleString = values.timezone
    ? `DTSTART;TZID=${values.timezone}${dateString}`
    : `DTSTART:${dateString}Z`;
  const rule = RRule.fromString(rruleString);

  return rule;
}

function pad(num) {
  if (typeof num === 'string') {
    return num;
  }
  return num < 10 ? `0${num}` : num;
}

export default function buildRuleObj(values, includeStart) {
  const ruleObj = {
    interval: values.interval || 1,
    freq: values.freq,
  };

  if (includeStart) {
    ruleObj.dtstart = buildDateTime(
      values.startDate,
      values.startTime,
      values.timezone
    );
  }

  return ruleObj;
}

function buildDateTime(dateString, timeString, timezone) {
  const localDate = DateTime.fromISO(`${dateString}T000000`, {
    zone: timezone,
  });
  const [hour, minute] = parseTime(timeString);
  const localTime = localDate.set({
    hour,
    minute,
    second: 0,
  });
  return localTime.toJSDate();
}
