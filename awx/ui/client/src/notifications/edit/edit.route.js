/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'notifications.edit',
    route: '/:notifier_id',
    templateUrl: templateUrl('notifications/edit/edit'),
    controller: 'notificationsEditController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        notifier:
        [   '$state',
            '$stateParams',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($state, $stateParams, $q, rest, getBasePath, ProcessErrors) {
                if ($stateParams.notifier) {
                    return $q.when($stateParams.notifier);
                }

                var notifierId = $stateParams.notifier_id;

                var url = getBasePath('notifiers') + notifierId + '/';
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
    },
    ncyBreadcrumb: {
        parent: 'notifications',
        label: 'Edit Notifier'
    }
};
