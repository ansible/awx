/* eslint-disable import/prefer-default-export */
import { getLanguage } from './language';

export function formatDateString(dateString, lang = getLanguage(navigator)) {
  return new Date(dateString).toLocaleString(lang);
}

export function secondsToHHMMSS(seconds) {
  return new Date(seconds * 1000).toISOString().substr(11, 8);
}
