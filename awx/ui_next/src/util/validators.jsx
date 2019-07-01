import { t } from '@lingui/macro';

export function required(message, i18n) {
  return value => {
    if (typeof value === 'string' && !value.trim()) {
      return message || i18n._(t`This field must not be blank`);
    }
    return undefined;
  };
}

export function maxLength(max, i18n) {
  return value => {
    if (value.trim().length > max) {
      return i18n._(t`This field must not exceed ${max} characters`);
    }
    return undefined;
  };
}

export function minMaxValue(min, max, i18n) {
  return value => {
    if (value < min || value > max) {
      return i18n._(
        t`This field must be a number and have a value between ${min} and ${max}`
      );
    }
    return undefined;
  };
}
