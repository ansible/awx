'use strict';

angular.module('frapontillo.ex.filters')
  .filter('lastNotNull', function() {
    return function(input) {
      if (input) {
        var l = input.length - 1;
        for (var i = l; i >= 0; i--) {
          if (input[i] !== undefined) {
            return input[i];
          }
        }
      }
    };
  }
);