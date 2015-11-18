/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 import getBrowserData from './browser-data.factory';
import ngApp from './ng-app.directive';

export default
    angular.module('browserData', [])
        .directive('ngApp', ngApp)
        .factory('browserData', getBrowserData);
