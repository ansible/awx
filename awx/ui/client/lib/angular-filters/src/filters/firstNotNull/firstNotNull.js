'use strict';

angular.module('frapontillo.ex.filters')
  .filter('firstNotNull', function() {
    return function(input) {
      if (input) {
        var l = input.length - 1;
        for (var i = 0; i <= l; i++) {
          if (input[i] !== undefined && input[i] !== null) {
            return input[i];
          }
        }
      }
    };
  }
);