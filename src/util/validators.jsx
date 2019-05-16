import { t } from '@lingui/macro';

export function required (message, i18n) {
  return value => {
    if (!value.trim()) {
      return message || i18n._(t`This field must not be blank`);
    }
    return undefined;
  };
}

export function maxLength (max, i18n) {
  return value => {
    if (value.trim().length
     > max) {
      return i18n._(t`This field must not exceed ${max} characters`);
    }
    return undefined;
  };
}
