import { getArticle, toTitleCase } from './strings';

describe('string utils', () => {
  describe('getArticle', () => {
    test('should return "a"', () => {
      expect(getArticle('team')).toEqual('a');
      expect(getArticle('notification')).toEqual('a');
    });

    test('should return "an"', () => {
      expect(getArticle('aardvark')).toEqual('an');
      expect(getArticle('ear')).toEqual('an');
      expect(getArticle('interest')).toEqual('an');
      expect(getArticle('ogre')).toEqual('an');
      expect(getArticle('umbrella')).toEqual('an');
    });
  });

  describe('toTitleCase', () => {
    test('should upper case each word', () => {
      expect(toTitleCase('a_string_of_words')).toEqual('A String Of Words');
    });

    test('should return empty string for undefined', () => {
      expect(toTitleCase(undefined)).toEqual('');
    });
  });
});
