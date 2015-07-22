/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'managementJobsList',
    route: '/management_jobs',
    templateUrl: '/static/js/management-jobs/list/list.partial.html',
    controller: 'listController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
