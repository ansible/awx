import { getLanguage } from './RootProvider';

describe('RootProvider.jsx', () => {
  test('getLanguage returns the expected language code', () => {
    expect(getLanguage({ languages: ['es-US'] })).toEqual('es');
    expect(getLanguage({ languages: ['es-US'], language: 'fr-FR', userLanguage: 'en-US' })).toEqual('es');
    expect(getLanguage({ language: 'fr-FR', userLanguage: 'en-US' })).toEqual('fr');
    expect(getLanguage({ userLanguage: 'en-US' })).toEqual('en');
  });
});
