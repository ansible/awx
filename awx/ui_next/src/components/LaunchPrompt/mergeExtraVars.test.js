import mergeExtraVars from './mergeExtraVars';

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
});
