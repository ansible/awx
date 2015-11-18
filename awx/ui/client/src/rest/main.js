/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import restServicesFactory from './restServices.factory';
import interceptors from './interceptors.service';
import fieldChoices from './get-choices.factory';
import fieldLabels from './get-labels.factory';

export default
    angular.module('RestServices', [])
        .config(['$httpProvider', function($httpProvider) {
            $httpProvider.interceptors.push('RestInterceptor');
        }])
        .factory('Rest', restServicesFactory)
        .service('RestInterceptor', interceptors)
        .factory('fieldChoices', fieldChoices)
        .factory('fieldLabels', fieldLabels);
