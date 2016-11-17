/* jshint ignore:start */

var sprintf = require('sprintf-js').sprintf;

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
            var langInfo = $window.navigator.language ||
                    $window.navigator.userLanguage;
            var langUrl = langInfo.replace('-', '_');
            //gettextCatalog.debug = true;
            gettextCatalog.setCurrentLanguage(langInfo);
            // TODO: the line below is commented out temporarily until
            // the .po files are received from the i18n team, in order to avoid
            // 404 file not found console errors in dev
            // gettextCatalog.loadRemote('/static/languages/' + langUrl + '.json');
        };
    }])
    .factory('i18n', ['gettextCatalog',
    function (gettextCatalog) {
        return {
            _: function (s) { return gettextCatalog.getString (s); },
            N_: N_,
            sprintf: sprintf,
            hasTranslation: function () {
                return gettextCatalog.strings[gettextCatalog.currentLanguage] !== undefined;
            }
        };
    }]);
