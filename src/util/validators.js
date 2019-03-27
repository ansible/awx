import { i18nMark } from '@lingui/react';

export function required (message) {
  return value => {
    if (!value.trim()) {
      return message || i18nMark('This field must not be blank');
    }
    return undefined;
  };
}

export function maxLength (max) {
  return value => {
    if (value.trim() > max) {
      return i18nMark(`This field must not exceed ${max} characters`);
    }
    return undefined;
  };
}
