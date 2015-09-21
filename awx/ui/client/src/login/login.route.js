/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'signIn',
    route: '/login',
    templateUrl: templateUrl('login/loginScreen'), //templateUrl('management-jobs/schedule/schedule'),
    // controller: 'authenticationController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
