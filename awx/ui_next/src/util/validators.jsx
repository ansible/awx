import { t } from '@lingui/macro';

export function required(message, i18n) {
  const errorMessage = message || i18n._(t`This field must not be blank`);
  return value => {
    if (typeof value === 'string' && !value.trim()) {
      return errorMessage;
    }
    if (typeof value === 'number' && !Number.isNaN(value)) {
      return undefined;
    }
    if (!value) {
      return errorMessage;
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

export function minLength(min, i18n) {
  return value => {
    if (value.trim().length < min) {
      return i18n._(t`This field must be at least ${min} characters`);
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

export function requiredEmail(i18n) {
  return value => {
    if (!value) {
      return i18n._(t`This field must not be blank`);
    }
    if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(value)) {
      return i18n._(t`Invalid email address`);
    }
    return undefined;
  };
}

export function noWhiteSpace(i18n) {
  return value => {
    if (/\s/.test(value)) {
      return i18n._(t`This field must not contain spaces`);
    }
    return undefined;
  };
}

export function integer(i18n) {
  return value => {
    const str = String(value);
    if (/[^0-9]/.test(str)) {
      return i18n._(t`This field must be an integer`);
    }
    return undefined;
  };
}

export function number(i18n) {
  return value => {
    const str = String(value);
    if (/^-?[0-9]*(\.[0-9]*)?$/.test(str)) {
      return undefined;
    }
    // large number scientific notation (e.g. '1e+21')
    if (/^-?[0-9]*e[+-][0-9]*$/.test(str)) {
      return undefined;
    }
    return i18n._(t`This field must be a number`);
  };
}

export function url(i18n) {
  return value => {
    if (!value) {
      return undefined;
    }
    // URL regex from https://urlregex.com/
    if (
      // eslint-disable-next-line max-len
      !/((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=+$,\w]+@)?[A-Za-z0-9.-]+|(?:www\.|[-;:&=+$,\w]+@)[A-Za-z0-9.-]+)((?:\/[+~%/.\w\-_]*)?\??(?:[-+=&;%@.\w_]*)#?(?:[.!/\\\w]*))?)/.test(
        value
      )
    ) {
      return i18n._(t`Please enter a valid URL`);
    }
    return undefined;
  };
}

export function combine(validators) {
  return value => {
    for (let i = 0; i < validators.length; i++) {
      const validate = validators[i];
      const error = validate ? validate(value) : null;
      if (error) {
        return error;
      }
    }
    return undefined;
  };
}

export function regExp(i18n) {
  return value => {
    try {
      RegExp(value);
    } catch {
      return i18n._(t`This field must be a regular expression`);
    }
    return undefined;
  };
}
