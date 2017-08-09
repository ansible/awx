/* jshint ignore:start */

var sprintf = require('sprintf-js').sprintf;
let defaultLanguage = 'en_US';

/**
 * @ngdoc method
 * @name function:i18n#N_
 * @methodOf function:N_
 * @description this function marks the translatable string with N_
 *  for 'grunt nggettext_extract'
 *
*/
export function N_(s) {
    return s;
}

export default
    angular.module('I18N', [])
    .factory('I18NInit', ['$window', 'gettextCatalog',
    function ($window, gettextCatalog) {
        return function() {
            var langInfo = ($window.navigator.languages || [])[0] ||
                    $window.navigator.language ||
                    $window.navigator.userLanguage ||
                    '';
            var langUrl = langInfo.replace('-', '_');

            if (langUrl === defaultLanguage) {
                return;
            }

            // gettextCatalog.debug = true;
            gettextCatalog.setCurrentLanguage(langInfo);
            gettextCatalog.loadRemote('/static/languages/' + langUrl + '.json');
        };
    }])
    .factory('i18n', ['gettextCatalog',
    function (gettextCatalog) {
        return {
            _: function (s) { return gettextCatalog.getString (s); },
            N_: N_,
            translate: (singular, context) => gettextCatalog.getString(singular, context),
            translatePlural: (count, singular, plural, context) => {
                return gettextCatalog.getPlural(count, singular, plural, context);
            },
            sprintf: sprintf,
            hasTranslation: function () {
                return gettextCatalog.strings[gettextCatalog.currentLanguage] !== undefined;
            }
        };
    }]);
