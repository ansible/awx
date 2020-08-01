import mergeExtraVars, { maskPasswords } from './mergeExtraVars';

describe('mergeExtraVars', () => {
  test('should handle yaml string', () => {
    const yaml = '---\none: 1\ntwo: 2';
    expect(mergeExtraVars(yaml)).toEqual({
      one: 1,
      two: 2,
    });
  });

  test('should handle json string', () => {
    const jsonString = '{"one": 1, "two": 2}';
    expect(mergeExtraVars(jsonString)).toEqual({
      one: 1,
      two: 2,
    });
  });

  test('should handle empty string', () => {
    expect(mergeExtraVars('')).toEqual({});
  });

  test('should merge survey results into extra vars object', () => {
    const yaml = '---\none: 1\ntwo: 2';
    const survey = { foo: 'bar', bar: 'baz' };
    expect(mergeExtraVars(yaml, survey)).toEqual({
      one: 1,
      two: 2,
      foo: 'bar',
      bar: 'baz',
    });
  });

  test('should handle undefined', () => {
    expect(mergeExtraVars(undefined, undefined)).toEqual({});
  });

  describe('maskPasswords', () => {
    test('should mask password fields', () => {
      const vars = {
        one: 'alpha',
        two: 'bravo',
        three: 'charlie',
      };

      expect(maskPasswords(vars, ['one', 'three'])).toEqual({
        one: '········',
        two: 'bravo',
        three: '········',
      });
    });

    test('should mask empty strings', () => {
      const vars = {
        one: '',
        two: 'bravo',
      };

      expect(maskPasswords(vars, ['one', 'three'])).toEqual({
        one: '········',
        two: 'bravo',
      });
    });
  });
});
