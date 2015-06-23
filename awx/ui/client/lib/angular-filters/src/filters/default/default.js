'use strict';

angular.module('frapontillo.ex.filters')
  .filter('default', function() {
    return function(input, value) {
      if (!isNaN(input) && input !== null && input !== undefined && (input !== '' || angular.isNumber(input))) {
        return input;
      }
      return value || '';
    };
  }
);
