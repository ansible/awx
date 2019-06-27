import { pluralize, getArticle, ucFirst } from './strings';

describe('string utils', () => {
  describe('pluralize', () => {
    test('should add an "s"', () => {
      expect(pluralize('team')).toEqual('teams');
    });

    test('should add an "es"', () => {
      expect(pluralize('class')).toEqual('classes');
    });
  });

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

  describe('ucFirst', () => {
    test('should capitalize first character', () => {
      expect(ucFirst('team')).toEqual('Team');
    });
  });
});
