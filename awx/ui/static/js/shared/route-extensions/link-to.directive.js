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
                   <link-to route="post" model="{ id: featuredPost }">
                       {{featuredPost.title}}
                   </link-to>
                </section>
           </file>
        </example>
 *
 */
export default
    [   '$route',
        'transitionTo',
        function($routeProvider, transitionTo) {
            return {
                restrict: 'E',
                transclude: true,
                template: '<a href="{{url}}" data-transition-to title="{{routeName}}" ng-transclude></a>',
                scope: {
                    routeName: '@route',
                    model: '&'
                },
                link: function(scope, element, attrs) {

                    var model = scope.$eval(scope.model);
                    scope.url = lookupRouteUrl(scope.routeName, $routeProvider.routes, model);

                    element.find('[data-transition-to]').on('click', function(e) {
                        e.stopPropagation();
                        e.preventDefault();
                        transitionTo(scope.routeName, model);
                    });

                }
            };
        }
    ]
