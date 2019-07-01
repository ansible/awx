import { required, maxLength } from './validators';

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
});
