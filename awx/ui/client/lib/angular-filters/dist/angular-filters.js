/**
 * A collection of filters for AngularJS.
 * @version v1.1.2 - 2015-06-13
 * @author Francesco Pontillo
 * @link https://github.com/frapontillo/angular-filters
 * @license Apache License 2.0
**/

'use strict';
// Source: common/module.js
angular.module('frapontillo.ex.filters', []);
angular.module('frapontillo', ['ex.filters']);
// Source: dist/.temp/filters/bool/bool.js
angular.module('frapontillo.ex.filters').filter('bool', function () {
  return function (input, valueTrue, valueFalse) {
    return input !== true ? valueFalse : valueTrue;
  };
});
// Source: dist/.temp/filters/default/default.js
angular.module('frapontillo.ex.filters').filter('default', function () {
  return function (input, value) {
    if (!isNaN(input) && input !== null && input !== undefined && (input !== '' || angular.isNumber(input))) {
      return input;
    }
    return value || '';
  };
});
// Source: dist/.temp/filters/firstNotNull/firstNotNull.js
angular.module('frapontillo.ex.filters').filter('firstNotNull', function () {
  return function (input) {
    if (input) {
      var l = input.length - 1;
      for (var i = 0; i <= l; i++) {
        if (input[i] !== undefined && input[i] !== null) {
          return input[i];
        }
      }
    }
  };
});
// Source: dist/.temp/filters/join/join.js
angular.module('frapontillo.ex.filters').filter('join', function () {
  return function (array, separator) {
    if (!array) {
      return '';
    }
    return array.join(separator);
  };
});
// Source: dist/.temp/filters/lastNotNull/lastNotNull.js
angular.module('frapontillo.ex.filters').filter('lastNotNull', function () {
  return function (input) {
    if (input) {
      var l = input.length - 1;
      for (var i = l; i >= 0; i--) {
        if (input[i] !== undefined) {
          return input[i];
        }
      }
    }
  };
});
// Source: dist/.temp/filters/max/max.js
angular.module('frapontillo.ex.filters').filter('max', function () {
  return function (input) {
    var out;
    if (input) {
      for (var i in input) {
        if (input[i] > out || out === undefined || out === null) {
          out = input[i];
        }
      }
    }
    return out;
  };
});
// Source: dist/.temp/filters/min/min.js
angular.module('frapontillo.ex.filters').filter('min', function () {
  return function (input) {
    var out;
    if (input) {
      for (var i in input) {
        if (input[i] < out || out === undefined || out === null) {
          out = input[i];
        }
      }
    }
    return out;
  };
});
// Source: dist/.temp/filters/property/property.js
angular.module('frapontillo.ex.filters').filter('property', function () {
  return function (array, property) {
    var newArray = [];
    angular.forEach(array, function (element) {
      var evalProperty = element[property];
      newArray.push(evalProperty);
    });
    return newArray;
  };
});