/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import linkTo from './link-to.directive';
import transitionTo from './transition-to.factory';
import modelListener from './model-listener.config';

/**
 * @ngdoc overview
 * @name routeExtensions
 * @description
 *
 * # routeExtensions
 *
 *  Adds a couple useful features to ngRoute:
 *  - Adds a `name` property to route objects; used to identify the route in transitions & links
 *  - Adds the ability to pass model data when clicking a link that goes to a route
 *  - Adds a directive that generates a route's URL from the route name & given models
 *  - Adds the ability to specify models in route resolvers
 *
 *  ## Usage
 *
 *  If you need to generate a link to a route, then use the {@link routeExtensions.directive:linkTo `linkTo directive`}. If you need to transition to a route in JavaScript code, then use the {@link routeExtensions.factory:transitionTo `transitionTo service`}.
 *
*/
export default
    angular.module('routeExtensions',
                   ['ngRoute'])
        .factory('transitionTo', transitionTo)
        .run(modelListener)
        .directive('linkTo', linkTo);
