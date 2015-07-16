# angular-md5 [![Build Status](https://travis-ci.org/gdi2290/angular-md5.png?branch=master)](https://travis-ci.org/gdi2290/angular-md5)
md5 for Angular.js and Gravatar filter

#How do I add this to my project?

You can download angular-md5 by:

* (prefered) Using bower and running `bower install angular-md5 --save`
* Using npm and running `npm install angular-md5 --save`
* Downloading it manually by clicking [here to download development unminified version](https://raw.github.com/gdi2290/angular-md5/master/angular-md5.js)


````html
<body ng-app="YOUR_APP" ng-controller="MainCtrl">
  <img src="http://www.gravatar.com/avatar/{{ email | gravatar }}">
  <input type="email" ng-model="email" placeholder="Email Address">
  {{ message }}
</body>
<script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.2.0-rc.2/angular.min.js"></script>
<script src="app/bower_components/angular-md5/angular-md5.js"></script>
<script>
  angular.module('YOUR_APP', [
    'angular-md5', // you may also use 'ngMd5' or 'gdi2290.md5'
    'controllers'
  ]);
  angular.module('controllers', [])
    .controller('MainCtrl', ['$scope', 'md5', function($scope, md5) {

      $scope.$watch('email' ,function() {
        $scope.message = 'Your email Hash is: ' + md5.createHash($scope.email || '');
      });

    }]);
</script>

````
