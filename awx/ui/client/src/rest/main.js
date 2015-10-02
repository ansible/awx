/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import restServicesFactory from './restServices.factory';
import interceptors from './interceptors.service';

export default
    angular.module('RestServices', [])
        .config(['$httpProvider', function($httpProvider) {
            $httpProvider.interceptors.push('RestInterceptor');
        }])
        .factory('Rest', restServicesFactory)
        .service('RestInterceptor', interceptors);
