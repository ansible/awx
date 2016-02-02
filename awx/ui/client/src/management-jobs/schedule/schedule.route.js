/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'managementJobsSchedule',
    route: '/management_jobs/:management_job_id/schedules',
    templateUrl: templateUrl('management-jobs/schedule/schedule'),
    controller: 'managementJobsScheduleController',
    data: {
        activityStream: true,
        activityStreamTarget: 'schedule'
    },
    params: {management_job: null},
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        management_job:
        [   '$stateParams',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($stateParams, $q, rest, getBasePath, ProcessErrors) {
                if ($stateParams.management_job) {
                    return $q.when($stateParams.management_job);
                }

                var managementJobId = $stateParams.management_job_id;

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
