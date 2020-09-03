/* eslint-disable import/prefer-default-export */
import { t } from '@lingui/macro';
import { RRule } from 'rrule';
import { getLanguage } from './language';

const prependZeros = value => value.toString().padStart(2, 0);

export function formatDateString(dateString, lang = getLanguage(navigator)) {
  return new Date(dateString).toLocaleString(lang);
}

export function formatDateStringUTC(dateString, lang = getLanguage(navigator)) {
  return new Date(dateString).toLocaleString(lang, { timeZone: 'UTC' });
}

export function secondsToHHMMSS(seconds) {
  return new Date(seconds * 1000).toISOString().substr(11, 8);
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
  // input type="date-time" expects values to be formatted
  // like: YYYY-MM-DDTHH-MM-SS
  const year = dateObj.getFullYear();
  const month = prependZeros(dateObj.getMonth() + 1);
  const day = prependZeros(dateObj.getDate());
  const hour = prependZeros(dateObj.getHours());
  const minute = prependZeros(dateObj.getMinutes());
  const second = prependZeros(dateObj.getSeconds());
  return `${year}-${month}-${day}T${hour}:${minute}:${second}`;
}

export function getRRuleDayConstants(dayString, i18n) {
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
      throw new Error(i18n._(t`Unrecognized day string`));
  }
}
