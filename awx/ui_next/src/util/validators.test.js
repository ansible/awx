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
} from './validators';

const i18n = { _: val => val };

describe('validators', () => {
  test('required returns undefined if value given', () => {
    expect(required(null, i18n)('some value')).toBeUndefined();
    expect(required('oops', i18n)('some value')).toBeUndefined();
  });

  test('required returns default message if value missing', () => {
    expect(required(null, i18n)('')).toEqual({
      id: 'This field must not be blank',
    });
  });

  test('required returns custom message if value missing', () => {
    expect(required('oops', i18n)('')).toEqual('oops');
  });

  test('required interprets white space as empty value', () => {
    expect(required(null, i18n)(' ')).toEqual({
      id: 'This field must not be blank',
    });
    expect(required(null, i18n)('\t')).toEqual({
      id: 'This field must not be blank',
    });
  });

  test('required interprets undefined as empty value', () => {
    expect(required(null, i18n)(undefined)).toEqual({
      id: 'This field must not be blank',
    });
  });

  test('required interprets 0 as non-empty value', () => {
    expect(required(null, i18n)(0)).toBeUndefined();
  });

  test('maxLength accepts value below max', () => {
    expect(maxLength(10, i18n)('snazzy')).toBeUndefined();
  });

  test('maxLength accepts value equal to max', () => {
    expect(maxLength(10, i18n)('abracadbra')).toBeUndefined();
  });

  test('maxLength rejects value above max', () => {
    expect(maxLength(8, i18n)('abracadbra')).toEqual({
      id: 'This field must not exceed {max} characters',
      values: { max: 8 },
    });
  });

  test('minLength accepts value above min', () => {
    expect(minLength(3, i18n)('snazzy')).toBeUndefined();
  });

  test('minLength accepts value equal to min', () => {
    expect(minLength(10, i18n)('abracadbra')).toBeUndefined();
  });

  test('minLength rejects value below min', () => {
    expect(minLength(12, i18n)('abracadbra')).toEqual({
      id: 'This field must be at least {min} characters',
      values: { min: 12 },
    });
  });

  test('noWhiteSpace returns error', () => {
    expect(noWhiteSpace(i18n)('this has spaces')).toEqual({
      id: 'This field must not contain spaces',
    });
    expect(noWhiteSpace(i18n)('this has\twhitespace')).toEqual({
      id: 'This field must not contain spaces',
    });
    expect(noWhiteSpace(i18n)('this\nhas\nnewlines')).toEqual({
      id: 'This field must not contain spaces',
    });
  });

  test('noWhiteSpace should accept valid string', () => {
    expect(noWhiteSpace(i18n)('this_has_no_whitespace')).toBeUndefined();
  });

  test('integer should accept integer (number)', () => {
    expect(integer(i18n)(13)).toBeUndefined();
  });

  test('integer should accept integer (string)', () => {
    expect(integer(i18n)('13')).toBeUndefined();
  });

  test('integer should reject decimal/float', () => {
    expect(integer(i18n)(13.1)).toEqual({
      id: 'This field must be an integer',
    });
  });

  test('integer should reject string containing alphanum', () => {
    expect(integer(i18n)('15a')).toEqual({
      id: 'This field must be an integer',
    });
  });

  test('number should accept number (number)', () => {
    expect(number(i18n)(13)).toBeUndefined();
  });

  test('number should accept number (string)', () => {
    expect(number(i18n)('13')).toBeUndefined();
  });

  test('number should accept negative number', () => {
    expect(number(i18n)(-14)).toBeUndefined();
  });

  test('number should accept decimal/float', () => {
    expect(number(i18n)(13.1)).toBeUndefined();
  });

  test('number should accept large number', () => {
    expect(number(i18n)(999999999999999999999.9)).toBeUndefined();
    expect(number(i18n)(-999999999999999999999.9)).toBeUndefined();
  });

  test('number should reject string containing alphanum', () => {
    expect(number(i18n)('15a')).toEqual({
      id: 'This field must be a number',
    });
  });

  test('url should reject incomplete url', () => {
    expect(url(i18n)('abcd')).toEqual({
      id: 'Please enter a valid URL',
    });
  });

  test('url should accept fully qualified url', () => {
    expect(url(i18n)('http://example.com/foo')).toBeUndefined();
  });

  test('url should accept url with query params', () => {
    expect(url(i18n)('https://example.com/foo?bar=baz')).toBeUndefined();
  });

  test('url should reject short protocol', () => {
    expect(url(i18n)('h://example.com/foo')).toEqual({
      id: 'Please enter a valid URL',
    });
  });

  test('combine should run all validators', () => {
    const validators = [required(null, i18n), noWhiteSpace(i18n)];
    expect(combine(validators)('')).toEqual({
      id: 'This field must not be blank',
    });
    expect(combine(validators)('one two')).toEqual({
      id: 'This field must not contain spaces',
    });
    expect(combine(validators)('ok')).toBeUndefined();
  });

  test('combine should skip null validators', () => {
    const validators = [required(null, i18n), null];
    expect(combine(validators)('')).toEqual({
      id: 'This field must not be blank',
    });
    expect(combine(validators)('ok')).toBeUndefined();
  });

  test('regExp rejects invalid regular expression', () => {
    expect(regExp(i18n)('[')).toEqual({
      id: 'This field must be a regular expression',
    });
    expect(regExp(i18n)('')).toBeUndefined();
    expect(regExp(i18n)('ok')).toBeUndefined();
    expect(regExp(i18n)('[^a-zA-Z]')).toBeUndefined();
  });
});
