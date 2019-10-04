import { formatDateString } from './dates';

describe('formatDateString', () => {
  test('it returns the expected value', () => {
    const lang = 'en-US';
    expect(formatDateString('', lang)).toEqual('Invalid Date');
    expect(formatDateString({}, lang)).toEqual('Invalid Date');
    expect(formatDateString(undefined, lang)).toEqual('Invalid Date');
    expect(formatDateString('2018-01-31T01:14:52.969227Z', lang)).toEqual(
      '1/31/2018, 1:14:52 AM'
    );
  });
});
