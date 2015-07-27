'use strict';

angular.module('frapontillo.ex.filters')
  .filter('join', function() {
    return function(array, separator) {
      if (!array) {
        return '';
      }
      return array.join(separator);
    };
  }
);