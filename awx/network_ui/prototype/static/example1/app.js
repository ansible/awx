var app = angular.module('triangular', []);

var scope;

app.controller('MainCtrl', function($scope) {
  scope = $scope
  $scope.graph = {'width': window.innerWidth, 'height': window.innerHeight}
  $scope.circles = [
  	{'x': 15, 'y': 20, 'r':15},
  	{'x': 50, 'y': 60, 'r':20},
  	{'x': 80, 'y': 10, 'r':10},
  ]
});
