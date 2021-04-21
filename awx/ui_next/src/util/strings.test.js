import { toTitleCase } from './strings';

describe('string utils', () => {
  describe('toTitleCase', () => {
    test('should upper case each word', () => {
      expect(toTitleCase('a_string_of_words')).toEqual('A String Of Words');
    });

    test('should return empty string for undefined', () => {
      expect(toTitleCase(undefined)).toEqual('');
    });
  });
});
