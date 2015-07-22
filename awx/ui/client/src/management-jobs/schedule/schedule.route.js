/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'managementJobsSchedule',
    route: '/management_jobs/:management_job/schedules',
    templateUrl: '/static/js/management-jobs/schedule/schedule.partial.html',
    controller: 'scheduleController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        management_job:
        [   '$route',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($route, $q, rest, getBasePath, ProcessErrors) {
                if ($route.current.hasModelKey('management_job')) {
                    return $q.when($route.current.params.model.management_job);
                }

                var managementJobId = $route.current.params.management_job;

                var url = getBasePath('system_job_templates') + managementJobId + '/';
                rest.setUrl(url);
                return rest.get()
                    .then(function(data) {
                        return data.data;
                    }).catch(function (response) {
                    ProcessErrors(null, response.data, response.status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to get inventory script info. GET returned status: ' +
                        response.status
                    });
                });
            }
        ]
    }
};
