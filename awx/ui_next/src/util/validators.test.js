import { i18n } from '@lingui/core';
import en from '../locales/en/messages';
import {
  required,
  minLength,
  maxLength,
  noWhiteSpace,
  integer,
  number,
  url,
  combine,
  regExp,
  requiredEmail,
  validateTime,
} from './validators';

describe('validators', () => {
  beforeAll(() => {
    i18n.loadLocaleData({ en: { plurals: en } });
    i18n.load({ en });
    i18n.activate('en');
  });

  test('required returns undefined if value given', () => {
    expect(required(null)('some value')).toBeUndefined();
    expect(required('oops')('some value')).toBeUndefined();
  });

  test('required returns default message if value missing', () => {
    expect(required(null)('')).toEqual('This field must not be blank');
  });

  test('required returns custom message if value missing', () => {
    expect(required('oops')('')).toEqual('oops');
  });

  test('required interprets white space as empty value', () => {
    expect(required(null)(' ')).toEqual('This field must not be blank');
    expect(required(null)('\t')).toEqual('This field must not be blank');
  });

  test('required interprets undefined as empty value', () => {
    expect(required(null)(undefined)).toEqual('This field must not be blank');
  });

  test('required interprets 0 as non-empty value', () => {
    expect(required(null)(0)).toBeUndefined();
  });

  test('maxLength accepts value below max', () => {
    expect(maxLength(10)('snazzy')).toBeUndefined();
  });

  test('maxLength accepts value equal to max', () => {
    expect(maxLength(10)('abracadbra')).toBeUndefined();
  });

  test('maxLength rejects value above max', () => {
    expect(maxLength(8)('abracadbra')).toEqual(
      'This field must not exceed 8 characters'
    );
  });

  test('minLength accepts value above min', () => {
    expect(minLength(3)('snazzy')).toBeUndefined();
  });

  test('minLength accepts value equal to min', () => {
    expect(minLength(10)('abracadbra')).toBeUndefined();
  });

  test('minLength rejects value below min', () => {
    expect(minLength(12)('abracadbra')).toEqual(
      'This field must be at least 12 characters'
    );
  });

  test('noWhiteSpace returns error', () => {
    expect(noWhiteSpace()('this has spaces')).toEqual(
      'This field must not contain spaces'
    );
    expect(noWhiteSpace()('this has\twhitespace')).toEqual(
      'This field must not contain spaces'
    );
    expect(noWhiteSpace()('this\nhas\nnewlines')).toEqual(
      'This field must not contain spaces'
    );
  });

  test('noWhiteSpace should accept valid string', () => {
    expect(noWhiteSpace()('this_has_no_whitespace')).toBeUndefined();
  });

  test('integer should accept integer (number)', () => {
    expect(integer()(13)).toBeUndefined();
  });

  test('integer should accept integer (string)', () => {
    expect(integer()('13')).toBeUndefined();
  });

  test('integer should reject decimal/float', () => {
    expect(integer()(13.1)).toEqual('This field must be an integer');
  });

  test('integer should reject string containing alphanum', () => {
    expect(integer()('15a')).toEqual('This field must be an integer');
  });

  test('number should accept number (number)', () => {
    expect(number()(13)).toBeUndefined();
  });

  test('number should accept number (string)', () => {
    expect(number()('13')).toBeUndefined();
  });

  test('number should accept negative number', () => {
    expect(number()(-14)).toBeUndefined();
  });

  test('number should accept decimal/float', () => {
    expect(number()(13.1)).toBeUndefined();
  });

  test('number should accept large number', () => {
    expect(number()(999999999999999999999.9)).toBeUndefined();
    expect(number()(-999999999999999999999.9)).toBeUndefined();
  });

  test('number should reject string containing alphanum', () => {
    expect(number()('15a')).toEqual('This field must be a number');
  });

  test('url should reject incomplete url', () => {
    expect(url()('abcd')).toEqual('Please enter a valid URL');
  });

  test('url should accept fully qualified url', () => {
    expect(url()('http://example.com/foo')).toBeUndefined();
  });

  test('url should accept url with query params', () => {
    expect(url()('https://example.com/foo?bar=baz')).toBeUndefined();
  });

  test('url should reject short protocol', () => {
    expect(url()('h://example.com/foo')).toEqual('Please enter a valid URL');
  });

  test('combine should run all validators', () => {
    const validators = [required(null), noWhiteSpace()];
    expect(combine(validators)('')).toEqual('This field must not be blank');
    expect(combine(validators)('one two')).toEqual(
      'This field must not contain spaces'
    );
    expect(combine(validators)('ok')).toBeUndefined();
  });

  test('combine should skip null validators', () => {
    const validators = [required(null), null];
    expect(combine(validators)('')).toEqual('This field must not be blank');
    expect(combine(validators)('ok')).toBeUndefined();
  });

  test('regExp rejects invalid regular expression', () => {
    expect(regExp()('[')).toEqual('This field must be a regular expression');
    expect(regExp()('')).toBeUndefined();
    expect(regExp()('ok')).toBeUndefined();
    expect(regExp()('[^a-zA-Z]')).toBeUndefined();
  });

  test('email validator rejects obviously invalid email ', () => {
    expect(requiredEmail()('foobar321')).toEqual('Invalid email address');
  });

  test('bob has email', () => {
    expect(requiredEmail()('bob@localhost')).toBeUndefined();
  });

  test('validate time validates properly', () => {
    expect(validateTime()('12:15 PM')).toBeUndefined();
    expect(validateTime()('1:15 PM')).toBeUndefined();
    expect(validateTime()('01:15 PM')).toBeUndefined();
    expect(validateTime()('12:15')).toBeUndefined();
    expect(validateTime()('12:15: PM')).toEqual('Invalid time format');
    expect(validateTime()('12.15 PM')).toEqual('Invalid time format');
    expect(validateTime()('12;15 PM')).toEqual('Invalid time format');
  });
});
