/* eslint-disable import/prefer-default-export */
import { getLanguage } from './language';

export function formatDateString(dateString, lang = getLanguage(navigator)) {
  return new Date(dateString).toLocaleString(lang);
}
