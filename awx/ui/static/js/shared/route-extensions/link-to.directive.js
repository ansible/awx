/* jshint unused: vars */

import {lookupRouteUrl} from './lookup-route-url';

/**
 *
 *  @ngdoc directive
 *  @name routeExtensions.directive:linkTo
 *  @desription
 *      The `linkTo` directive looks up a route's URL and generates a link to that route. When a user
 *      clicks the link, this directive calls the `transitionTo` factory to send them to the given
 *      URL. For accessibility and fallback purposes, it also sets the `href` attribute of the link
 *      to the path.
 *
 *      Note that in this example the model object uses a key that matches up with the route parameteer
 *      name in the route url (in this case `:id`).
 *
 *  **N.B.** The below example currently won't run. It's included to show an example of using
 *  the `linkTo` directive within code. In order for this to run, we will need to run
 *  the code in an iframe (using something like `dgeni` instead of `grunt-ngdocs`).
 *
 *      @example
 *
       <example module="simpleRouteExample">
            <file name="script.js">
                angular.module('simpleRouteExample', ['ngRoute', 'routeExtensions'])
                    .config(['$routeProvider', function($route) {
                        $route.when('/posts/:id', {
                            name: 'post',
                            template: '<h1>{{post.title}}</h1><p>{{post.body}}</p>',
                            controller: 'post'
                        });
                    }]).controller('post', function($scope) {
                    });
            </file>
           <file name="index.html">
                <section ng-init="featuredPost =
                                    {   id: 1,
                                        title: 'Featured',
                                        body: 'This post is featured because it is awesome'
                                    };">
                   <a link-to="post" model="{ id: featuredPost }">
                       {{featuredPost.title}}
                   </a>
                </section>
           </file>
        </example>
 *
 */
export default
    [   '$route',
        '$location',
        'transitionTo',
        function($routeProvider, $location, transitionTo) {

            function transitionListener(routeName, model, e) {
                e.stopPropagation();
                e.preventDefault();
                transitionTo(routeName, model);
            }
            return {
                restrict: 'A',
                scope: {
                    routeName: '@linkTo',
                    model: '&'
                },
                link: function (scope, element, attrs) {

                    var listener;

                    scope.$watch(function() {
                        var model = scope.$eval(scope.model);
                        return model;
                    }, function(newValue) {

                        var model = scope.$eval(scope.model);
                        scope.url = lookupRouteUrl(scope.routeName, $routeProvider.routes, model, $location.$$html5);
                        element.off('click', listener);

                        listener = _.partial(transitionListener, scope.routeName, model);

                        element.on('click', listener);

                        element.attr('href', scope.url);
                    }, true);

                }
            };
        }
    ];
