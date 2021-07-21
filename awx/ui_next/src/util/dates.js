/* eslint-disable import/prefer-default-export */
import { t } from '@lingui/macro';
import { RRule } from 'rrule';
import { getLanguage } from './language';

const prependZeros = (value) => value.toString().padStart(2, 0);

export function formatDateString(dateString, lang = getLanguage(navigator)) {
  if (dateString === null) {
    return null;
  }
  return new Date(dateString).toLocaleString(lang);
}

export function formatDateStringUTC(dateString, lang = getLanguage(navigator)) {
  if (dateString === null) {
    return null;
  }
  return new Date(dateString).toLocaleString(lang, { timeZone: 'UTC' });
}

export function secondsToHHMMSS(seconds) {
  return new Date(seconds * 1000).toISOString().substr(11, 8);
}

export function secondsToDays(seconds) {
  let duration = Math.floor(parseInt(seconds, 10) / 86400);
  if (duration < 0) {
    duration = 0;
  }
  return duration.toString();
}

export function timeOfDay() {
  const date = new Date();
  const hour = date.getHours();
  const minute = prependZeros(date.getMinutes());
  const second = prependZeros(date.getSeconds());
  const time =
    hour > 12
      ? `${hour - 12}:${minute}:${second} PM`
      : `${hour}:${minute}:${second} AM`;
  return time;
}

export function dateToInputDateTime(dateObj) {
  let date = dateObj;
  if (typeof dateObj === 'string') {
    date = new Date(dateObj);
  }
  const year = date.getFullYear();
  const month = prependZeros(date.getMonth() + 1);
  const day = prependZeros(date.getDate());
  const hour =
    date.getHours() > 12 ? parseInt(date.getHours(), 10) - 12 : date.getHours();
  const minute = prependZeros(date.getMinutes());
  const amPmText = date.getHours() > 11 ? 'PM' : 'AM';

  return [`${year}-${month}-${day}`, `${hour}:${minute} ${amPmText}`];
}

export function getRRuleDayConstants(dayString) {
  switch (dayString) {
    case 'sunday':
      return RRule.SU;
    case 'monday':
      return RRule.MO;
    case 'tuesday':
      return RRule.TU;
    case 'wednesday':
      return RRule.WE;
    case 'thursday':
      return RRule.TH;
    case 'friday':
      return RRule.FR;
    case 'saturday':
      return RRule.SA;
    case 'day':
      return [
        RRule.MO,
        RRule.TU,
        RRule.WE,
        RRule.TH,
        RRule.FR,
        RRule.SA,
        RRule.SU,
      ];
    case 'weekday':
      return [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR];
    case 'weekendDay':
      return [RRule.SA, RRule.SU];
    default:
      throw new Error(t`Unrecognized day string`);
  }
}
