import { required, maxLength, noWhiteSpace, combine } from './validators';

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
});
