/* eslint-disable import/prefer-default-export */
import { t } from '@lingui/macro';
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

export function getDaysInMonth(dateString) {
  const dateObj = new Date(dateString);
  return new Date(dateObj.getFullYear(), dateObj.getMonth() + 1, 0).getDate();
}

export function getWeekNumber(dateString) {
  const dateObj = new Date(dateString);
  const dayOfMonth = dateObj.getDate();
  const dayOfWeek = dateObj.getDay();
  if (dayOfMonth < 8) {
    return 1;
  }
  dateObj.setDate(dayOfMonth - dayOfWeek + 1);
  return Math.ceil(dayOfMonth / 7);
}

export function getDayString(dayIndex, i18n) {
  switch (dayIndex) {
    case 0:
      return i18n._(t`Sunday`);
    case 1:
      return i18n._(t`Monday`);
    case 2:
      return i18n._(t`Tuesday`);
    case 3:
      return i18n._(t`Wednesday`);
    case 4:
      return i18n._(t`Thursday`);
    case 5:
      return i18n._(t`Friday`);
    case 6:
      return i18n._(t`Saturday`);
    default:
      throw new Error(i18n._(t`Unrecognized day index`));
  }
}

export function getWeekString(weekNumber, i18n) {
  switch (weekNumber) {
    case 1:
      return i18n._(t`first`);
    case 2:
      return i18n._(t`second`);
    case 3:
      return i18n._(t`third`);
    case 4:
      return i18n._(t`fourth`);
    case 5:
      return i18n._(t`fifth`);
    default:
      throw new Error(i18n._(t`Unrecognized week number`));
  }
}

export function getMonthString(monthIndex, i18n) {
  switch (monthIndex) {
    case 0:
      return i18n._(t`January`);
    case 1:
      return i18n._(t`February`);
    case 2:
      return i18n._(t`March`);
    case 3:
      return i18n._(t`April`);
    case 4:
      return i18n._(t`May`);
    case 5:
      return i18n._(t`June`);
    case 6:
      return i18n._(t`July`);
    case 7:
      return i18n._(t`August`);
    case 8:
      return i18n._(t`September`);
    case 9:
      return i18n._(t`October`);
    case 10:
      return i18n._(t`November`);
    case 11:
      return i18n._(t`December`);
    default:
      throw new Error(i18n._(t`Unrecognized month index`));
  }
}
