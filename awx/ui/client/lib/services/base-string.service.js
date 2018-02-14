import defaults from '~assets/default.strings.json';

let i18n;

function BaseStringService (namespace) {
    const ERROR_NO_NAMESPACE = 'BaseString cannot be extended without providing a namespace';

    if (!namespace) {
        throw new Error(ERROR_NO_NAMESPACE);
    }

    this[namespace] = {};
    this.t = {};

    /**
     * To translate a singular string by itself or a string with context data, use `translate`.
     * For brevity, this is renamed as `t.s` (as in "translate singular"). `t.s` serves a dual
     * purpose -- it's to mark strings for translation so they appear in the `.pot` file after
     * the grunt-angular-gettext task is run AND it's used to fetch the translated string at
     * runtime.
     *
     * NOTE: View ui/src/i18n.js for where these i18n methods are defined. i18n is a wrapper around
     * the library angular-gettext.
     *
     * @arg {string} string - The string to be translated
     * @arg {object=} context - A data object used to populate dynamic context data in a string.
     *
     * @returns {string} The translated string or the original string in the even the translation
     * does not exist.
     */
    this.t.s = i18n.translate;

    /**
     * To translate a plural string use `t.p`. The `count` supplied will determine whether the
     * singular or plural string is returned.
     *
     * @arg {number} count - The count of the plural object
     * @arg {string} singular - The singular version of the string to be translated
     * @arg {string} plural - The plural version of the string to be translated
     * @arg {object=} context - A data object used to populate dynamic context data in a string.
     *
     * @returns {string} The translated string or the original string in the even the translation
     * does not exist.
     */
    this.t.p = i18n.translatePlural;

    const { t } = this;

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
    this.CANCEL = t.s('CANCEL');
    this.SAVE = t.s('SAVE');
    this.OK = t.s('OK');
    this.NEXT = t.s('NEXT');
    this.SHOW = t.s('SHOW');
    this.HIDE = t.s('HIDE');
    this.ON = t.s('ON');
    this.OFF = t.s('OFF');
    this.YAML = t.s('YAML');
    this.JSON = t.s('JSON');
    this.DELETE = t.s('DELETE');
    this.COPY = t.s('COPY');

    this.deleteResource = {
        HEADER: t.s('Delete'),
        USED_BY: resourceType => t.s('The {{ resourceType }} is currently being used by other resources.', { resourceType }),
        CONFIRM: resourceType => t.s('Are you sure you want to delete this {{ resourceType }}?', { resourceType })
    };

    this.error = {
        HEADER: t.s('Error!'),
        CALL: ({ path, action, status }) => t.s('Call to {{ path }} failed. {{ action }} returned status: {{ status }}.', { path, action, status }),
    };

    this.ALERT = ({ header, body }) => t.s('{{ header }} {{ body }}', { header, body });

    /**
     * This getter searches the extending class' namespace first for a match then falls back to
     * the more globally relevant strings defined here. Strings with with dots as delimeters are
     * supported to give flexibility to extending classes to nest strings as necessary.
     *
     *
     * The `t.s` and `t.p` calls should only be used where strings are defined in
     * <name>.strings.js` files. To use translated strings elsewhere, access them through this
     * common interface.
     *
     * @arg {string} name - The property name of the string (e.g. 'CANCEL')
     * @arg {number=} count - A count of objects referenced in your plural string
     * @arg {object=} context - An object containing data to use in the interpolation of the string
     */
    this.get = (name, ...args) => {
        const keys = name.split('.');
        let value;

        keys.forEach(key => {
            if (!value) {
                value = this[namespace][key] || this[key];
            } else {
                value = value[key];
            }
        });

        if (!value || typeof value === 'string') {
            return value;
        }

        return value(...args);
    };
}

function BaseStringServiceLoader (_i18n_) {
    i18n = _i18n_;

    return BaseStringService;
}

BaseStringServiceLoader.$inject = ['i18n'];

export default BaseStringServiceLoader;
