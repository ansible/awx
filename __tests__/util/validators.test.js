import { required, maxLength } from '../../src/util/validators';

describe('validators', () => {
  test('required returns undefined if value given', () => {
    expect(required()('some value')).toBeUndefined();
    expect(required('oops')('some value')).toBeUndefined();
  });

  test('required returns default message if value missing', () => {
    expect(required()('')).toEqual('This field must not be blank');
  });

  test('required returns custom message if value missing', () => {
    expect(required('oops')('')).toEqual('oops');
  });

  test('required interprets white space as empty value', () => {
    expect(required()(' ')).toEqual('This field must not be blank');
    expect(required()('\t')).toEqual('This field must not be blank');
  });

  test('maxLength accepts value below max', () => {
    expect(maxLength(10)('snazzy')).toBeUndefined();
  });

  test('maxLength accepts value equal to max', () => {
    expect(maxLength(10)('abracadbra')).toBeUndefined();
  });

  test('maxLength rejects value above max', () => {
    expect(maxLength(8)('abracadbra'))
      .toEqual('This field must not exceed 8 characters');
  });
});
