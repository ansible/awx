angular.module('longDateFilter', []).filter('longDate', function() {
  return function(input) {
    var date = moment(input);
    return date.format('l LTS');
  };
});
