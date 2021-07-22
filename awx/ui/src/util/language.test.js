import { getLanguage, getLanguageWithoutRegionCode } from './language';

describe('getLanguage', () => {
  test('it returns the expected language code', () => {
    expect(getLanguage({ languages: ['es-US'] })).toEqual('es-US');
    expect(
      getLanguage({
        languages: ['es-US'],
        language: 'fr-FR',
        userLanguage: 'en-US',
      })
    ).toEqual('es-US');
    expect(getLanguage({ language: 'fr-FR', userLanguage: 'en-US' })).toEqual(
      'fr-FR'
    );
    expect(getLanguage({ userLanguage: 'en-US' })).toEqual('en-US');
  });
});

describe('getLanguageWithoutRegionCode', () => {
  test('it returns the expected (truncated) language code', () => {
    expect(getLanguageWithoutRegionCode({ languages: ['es-US'] })).toEqual(
      'es'
    );
    expect(
      getLanguageWithoutRegionCode({
        languages: ['es-US'],
        language: 'fr-FR',
        userLanguage: 'en-US',
      })
    ).toEqual('es');
    expect(
      getLanguageWithoutRegionCode({ language: 'fr-FR', userLanguage: 'en-US' })
    ).toEqual('fr');
    expect(getLanguageWithoutRegionCode({ userLanguage: 'en-US' })).toEqual(
      'en'
    );
  });
});
