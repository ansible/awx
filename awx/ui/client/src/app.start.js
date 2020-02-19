const SUPPORTED_LOCALES = ['en', 'es', 'fr', 'ja', 'nl', 'zh'];
const DEFAULT_LOCALE = 'en';
const BASE_PATH = global.$basePath ? `${global.$basePath}languages/` : '/static/languages/';

/**
 * The Angular app is manually initialized in order to complete some
 * asynchronous work up front. This function returns a callback so app.js can
 * call `angular.bootstrap` when the work is complete.
 *
 * @argument {function} - Callback.
 */
function bootstrap (callback) {
    fetchLocaleStrings((locale) => {
        if (locale) {
            angular.module('I18N').constant('LOCALE', locale);
        }

        fetchConfig(() => {
            angular.element(document).ready(() => callback());
        });
    });
}

/**
 * GET the localized JSON strings file or fall back to the default language
 * if the locale isn't supported or if the request fails.
 *
 * @argument {function} - Callback.
 *
 * @returns {object=} - Locale data if it exists.
 */
function fetchLocaleStrings (callback) {
    const code = getNormalizedLocaleCode();

    if (isDefaultLocale(code) || !isSupportedLocale(code)) {
        callback({ code });

        return;
    }

    const request = $.ajax(`${BASE_PATH}${code}.json`);

    request.done(res => {
        if (res[code]) {
            callback({ code, strings: res[code] });
        } else {
            callback({ code: DEFAULT_LOCALE });
        }
    });

    request.fail(() => callback({ code: DEFAULT_LOCALE }));
}

function fetchConfig (callback) {
    const request = $.ajax('/api/');

    request.done(res => {
        global.$ConfigResponse = res;
        if (res.login_redirect_override) {
            if (!document.cookie.split(';').filter((item) => item.includes('userLoggedIn=true')).length && !window.location.href.includes('/#/login')) {
                window.location.replace(res.login_redirect_override);
            } else {
                callback();
            }
        } else {
            callback();
        }
    });

    request.fail(() => callback());
}

/**
 * Grabs the language off of navigator for browser compatibility.
 * If the language isn't set, then it falls back to the DEFAULT_LOCALE. The
 * locale code is normalized to be lowercase and 2 characters in length.
 */
function getNormalizedLocaleCode () {
    let code;

    if (navigator.languages && navigator.languages[0]) {
        [code] = navigator.languages;
    } else if (navigator.language) {
        code = navigator.language;
    } else {
        code = navigator.userLanguage;
    }

    try {
        code = code.split('-')[0].toLowerCase();
    } catch (error) {
        code = DEFAULT_LOCALE;
    }

    return code.substring(0, 2);
}

function isSupportedLocale (code) {
    return SUPPORTED_LOCALES.includes(code);
}

function isDefaultLocale (code) {
    return code === DEFAULT_LOCALE;
}

export default {
    bootstrap
};
