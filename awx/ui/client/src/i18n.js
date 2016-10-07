function isString(arg) {
    return typeof arg === 'string';
}

function isNull(arg) {
    return arg === null;
}

function isObject(arg) {
    return typeof arg === 'object' && arg !== null;
}

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

// Copied format() from util/util.js. util.js includes "require()".
/**
 * @ngdoc method
 * @name function:i18n#format
 * @methodOf function:format
 * @description this function provides C-style's formatted sprintf().
 *
*/
export function format(f) {
    var i;
    var formatRegExp = /%[sdj%]/g;
    if (!isString(f)) {
        var objects = [];
        for (i = 0; i < arguments.length; i++) {
            objects.push(JSON.stringify(arguments[i]));
        }
        return objects.join(' ');
    }

    i = 1;
    var args = arguments;
    var len = args.length;
    var str = String(f).replace(formatRegExp, function(x) {
        if (x === '%%') return '%';
        if (i >= len) return x;
        switch (x) {
        case '%s': return String(args[i++]);
        case '%d': return Number(args[i++]);
        case '%j':
        case '%j':
            try {
                return JSON.stringify(args[i++]);
            } catch (_) {
                return '[Circular]';
            }
        default:
            return x;
        }
    });
    for (var x = args[i]; i < len; x = args[++i]) {
        if (isNull(x) || !isObject(x)) {
            str += ' ' + x;
        } else {
            str += ' ' + JSON.stringify(x);
        }
    }
    return str;
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
            gettextCatalog.loadRemote('/static/languages/' + langUrl + '.json');
        };
    }])
    .factory('i18n', ['gettextCatalog',
    function (gettextCatalog) {
        return {
            _: function (s) { return gettextCatalog.getString (s); },
            N_: N_,
            format: format,
            hasTranslation: function () {
                return gettextCatalog.strings[gettextCatalog.currentLanguage] !== undefined;
            }
        };
    }]);
