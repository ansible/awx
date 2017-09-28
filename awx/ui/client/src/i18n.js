import { sprintf } from 'sprintf-js';

function I18n (gettextCatalog) {
    return {
        N_,
        sprintf,
        _: s => gettextCatalog.getString(s),
        translate: (singular, context) => gettextCatalog.getString(singular, context),
        translatePlural: (count, singular, plural, context) => {
            return gettextCatalog.getPlural(count, singular, plural, context);
        },
        hasTranslation: () => gettextCatalog.strings[gettextCatalog.currentLanguage] !== undefined
    };
}

I18n.$inject = ['gettextCatalog'];

function run (LOCALE, gettextCatalog) {
    if (LOCALE.code && LOCALE.strings) {
        gettextCatalog.setCurrentLanguage(LOCALE.code);
        gettextCatalog.setStrings(LOCALE.code, LOCALE.strings);
    }
}

run.$inject = ['LOCALE', 'gettextCatalog'];

export function N_(s) {
    return s;
}

export default angular
    .module('I18N', [
        'gettext'
    ])
    .factory('i18n', I18n)
    .run(run);
