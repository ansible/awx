import defaults from '../../assets/default.strings.json';

let i18n;

function BaseStringService (namespace) {
    let t = i18n._;

    const ERROR_NO_NAMESPACE = t('BaseString cannot be extended without providing a namespace');
    const ERROR_NO_STRING = t('No string exists with this name');

    if (!namespace) {
        throw new Error(ERROR_NO_NAMESPACE);
    }

    this.t = t;
    this[namespace] = {};

    /*
     * These strings are globally relevant and configured to give priority to values in
     * default.strings.json and fall back to defaults defined inline.
     */
    this.BRAND_NAME = defaults.BRAND_NAME || 'AWX';
    this.PENDO_API_KEY = defaults.PENDO_API_KEY || '';

    /*
     * Globally relevant strings should be defined here to avoid duplication of content across the
     * the project.
     */
    this.CANCEL = t('CANCEL');
    this.SAVE = t('SAVE');
    this.OK = t('OK');

    /**
     * This getter searches the extending class' namespace first for a match then falls back to
     * the more globally relevant strings defined here. Strings with with dots as delimeters are
     * supported to give flexibility to extending classes to nest strings as necessary.
     *
     * If no match is found, an error is thrown to alert the developer immediately instead of
     * failing silently.
     */
    this.get = name => {
        let keys = name.split('.');
        let value;

        keys.forEach(key => {
            if (!value) {
                value = this[namespace][key] || this[key];
            } else {
                value = value[key];
            }

            if (!value) {
                throw new Error(ERROR_NO_STRING);
            }
        });

        return value;
    };
}

function BaseStringServiceLoader (_i18n_) {
    i18n = _i18n_;

    return BaseStringService;
}

BaseStringServiceLoader.$inject = ['i18n'];

export default BaseStringServiceLoader;
