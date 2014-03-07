'use strict';

angular.module('frapontillo.ex.filters')
  .filter('bool', function() {
    return function(input, valueTrue, valueFalse) {
      return input !== true ? valueFalse : valueTrue;
    };
  }
);