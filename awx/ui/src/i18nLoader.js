import { i18n } from '@lingui/core';
import { en, fr, es, ko, nl, ja, zh, zu } from 'make-plural/plurals';

export const locales = {
  en: 'English',
  ja: '日本語',
  zu: 'Zulu',
  fr: 'Français',
  es: 'Español',
  ko: '한국어',
  zh: '中文',
  nl: 'Nederlands',
};

i18n.loadLocaleData({
  en: { plurals: en },
  fr: { plurals: fr },
  es: { plurals: es },
  ko: { plurals: ko },
  nl: { plurals: nl },
  ja: { plurals: ja },
  zh: { plurals: zh },
  zu: { plurals: zu },
});

/**
 * We do a dynamic import of just the catalog that we need
 * @param locale any locale string
 */
export async function dynamicActivate(locale, pseudolocalization = false) {
  const { messages } = await import(`./locales/${locale}/messages`);

  if (pseudolocalization) {
    Object.keys(messages).forEach((key) => {
      if (Array.isArray(messages[key])) {
        // t`Foo ${param}` -> ["Foo ", ['param']] => [">>", "Foo ", ['param'], "<<"]
        messages[key] = ['»', ...messages[key], '«'];
      } else {
        // simple string
        messages[key] = `»${messages[key]}«`;
      }
    });
  }

  i18n.load(locale, messages);
  i18n.activate(locale);
}
