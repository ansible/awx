import {lookupRouteUrl} from './lookup-route-url';

/**
 * @ngdoc service
 * @name routeExtensions.service:transitionTo
 * @description
 *  The `transitionTo` service generates a URL given a route name and model parameters, then
 *  updates the browser's URL via `$location.path`. Use this in situations where you cannot
 *  use the `linkTo` directive, for example to redirect the user after saving an object.
 *
 *  @param {string} routeName The name of the route whose URL you want to redirect to (corresponds
 *                              name property of route)
 *  @param {object} model The model you want to use to generate the URL and be passed to the new
 *                          route. This object follows a strict key/value naming convention where
 *                          the keys match the parameters listed in the route's URL. For example,
 *                          a URL of `/posts/:id` would require a model object like: `{ id: post }`,
 *                          where `post` is the object you want to pass to the new route.
 *
 *  **N.B.** The below example currently won't run. It's included to show an example of using
 *  the `transitionTo` function within code. In order for this to run, we will need to run
 *  the code in an iframe (using something like `dgeni` instead of `grunt-ngdocs`).
 *
 *  @example
 *
     <example module="transitionToExample">
        <file name="script.js">
            angular.module('transitionToExample',
                           ['ngRoute',
                            'routeExtensions'
                           ])
                    .config(function($routeProvider, $locationProvider) {
                        $routeProvider
                            .when('/post/:id',
                                {   name: 'post',
                                    template: '<h1>{{post.title}}</h1><p>{{post.body}}</p>'
                                });

                        $locationProvider.html5Mode(true);
                        $locationProvider.hashPrefix('!');
                    })
                    .controller('post', ['$scope', function($scope) {

                    }])
                    .controller('postForm', ['$scope', 'transitionTo', function($scope, transitionTo) {
                        $scope.post = {
                            id: 1,
                            title: 'A post',
                            body: 'Some text'
                        };

                        $scope.savePost = function() {
                            transitionTo('post', { id: $scope.post });
                        }
                    }]);
        </file>
        <file name="index.html">
            <form ng-controller="postForm">
                <legend>Edit Post</legend>
                <label>
                    Title
                    <input type="text" ng-model="post.title">
                </label>
                <label>
                    Body
                    <textarea ng-model="post.body"></textarea>
                </label>

                <button ng-click="savePost()">Save Post</button>
            </form>
        </file>

    </example>

 */

function safeApply(fn, $rootScope) {
    var currentPhase = $rootScope.$$phase;

    if (currentPhase === '$apply' || currentPhase === '$digest') {
        fn();
    } else {
        $rootScope.$apply(fn);
    }
}

export default
    [  '$location',
        '$rootScope',
        '$route',
        '$q',
        function($location, $rootScope, $route, $q) {
            return function(routeName, model) {
                var deferred = $q.defer();
                var url = lookupRouteUrl(routeName, $route.routes, model, true);

                var offRouteChangeStart =
                    $rootScope.$on('$routeChangeStart', function(e, newRoute) {
                        if (newRoute.$$route.name === routeName) {
                            deferred.resolve(newRoute, model);
                            newRoute.params.model = model;
                        }

                        offRouteChangeStart();
                    });

                var offRouteChangeSuccess =
                    $rootScope.$on('$routeChangeSuccess', function(e, newRoute) {
                        if (newRoute.$$route.name === routeName) {
                            deferred.resolve(newRoute);
                        }

                        offRouteChangeSuccess();
                    });

                var offRouteChangeError =
                    $rootScope.$on('$routeChangeError', function(e, newRoute, previousRoute, rejection) {
                        if (newRoute.$$route.name === routeName) {
                            deferred.reject(newRoute, previousRoute, rejection);
                        }

                        offRouteChangeError();
                    });

                safeApply(function() {
                    $location.path(url);
                }, $rootScope);

                return deferred;
            };
        }
    ];
