/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail',
    url: '/jobs/:id',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: '{{ job.id }} - {{ job.name }}'
    },
    resolve: {
        jobData: ['Rest', 'GetBasePath', '$stateParams', '$q', '$state', 'Alert', function(Rest, GetBasePath, $stateParams, $q, $state, Alert) {
            Rest.setUrl(GetBasePath('jobs') + $stateParams.id);
            var val = $q.defer();
            Rest.get()
                .then(function(data) {
                    val.resolve(data.data);
                }, function(data) {
                    val.reject(data);

                    if (data.status === 404) {
                        Alert('Job Not Found', 'Cannot find job.', 'alert-info');
                    } else if (data.status === 403) {
                        Alert('Insufficient Permissions', 'You do not have permission to view this job.', 'alert-info');
                    }

                    $state.go('jobs');
                });
            return val.promise;
        }]
    },
    templateUrl: templateUrl('job-results/job-results'),
    controller: ['jobData', '$scope', function(jobData, $scope) {
        $scope.job = jobData;
    }]
};
