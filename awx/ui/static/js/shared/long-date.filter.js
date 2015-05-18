angular.module('longDateFilter', []).filter('longDate', function() {
  return function(input) {
    var date = moment(input).locale(navigator.language);
    return date.format('l LTS');
  };
});
