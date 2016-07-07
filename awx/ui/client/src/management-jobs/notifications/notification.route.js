/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'managementJobsList.notifications',
    route: '/:management_id/notifications',
    templateUrl: templateUrl('management-jobs/notifications/notifications'),
    controller: 'managementJobsNotificationsController',
    params: {card: null},
    resolve: {
        management_job:
        [   '$stateParams',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($stateParams, $q, rest, getBasePath, ProcessErrors) {

                if ($stateParams.card) {
                    return $q.when($stateParams.card);
                }

                var managementJobId = $stateParams.management_id;

                var url = getBasePath('system_job_templates') + managementJobId + '/';
                rest.setUrl(url);
                return rest.get()
                        .then(function(data) {
                            return data.data;
                        }).catch(function (response) {
            ProcessErrors(null, response.data, response.status, null, {
                hdr: 'Error!',
                msg: 'Failed to get management job info. GET returned status: ' +
                response.status
            });
        });
            }
        ]
    },
    ncyBreadcrumb: {
        parent: 'managementJobsList',
        label: 'NOTIFICATIONS'
    }
};
