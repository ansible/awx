import { i18n } from '@lingui/core';
import { en, fr, es, nl, ja, zh, zu } from 'make-plural/plurals';

export const locales = {
  en: 'English',
  ja: 'Japanese',
  zu: 'Zulu',
  fr: 'French',
  es: 'Spanish',
  zh: 'Chinese',
  nl: 'Dutch',
};

i18n.loadLocaleData({
  en: { plurals: en },
  fr: { plurals: fr },
  es: { plurals: es },
  nl: { plurals: nl },
  ja: { plurals: ja },
  zh: { plurals: zh },
  zu: { plurals: zu },
});

/**
 * We do a dynamic import of just the catalog that we need
 * @param locale any locale string
 */
export async function dynamicActivate(locale) {
  const { messages } = await import(`./locales/${locale}/messages`);
  i18n.load(locale, messages);
  i18n.activate(locale);
}
