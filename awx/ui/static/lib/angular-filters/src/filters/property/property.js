'use strict';

angular.module('frapontillo.ex.filters')
  .filter('property', function() {
    return function(array, property) {
      var newArray = [];
      // for each object in the array
      angular.forEach(array, function(element) {
        var evalProperty = element[property];
        newArray.push(evalProperty);
      });
      return newArray;
    };
  }
);