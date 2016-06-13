/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'notifications.edit',
    route: '/:notification_template_id',
    templateUrl: templateUrl('notifications/edit/edit'),
    controller: 'notificationsEditController',
    resolve: {
        notification_template:
        [   '$state',
            '$stateParams',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($state, $stateParams, $q, rest, getBasePath, ProcessErrors) {
                if ($stateParams.notification_template) {
                    return $q.when($stateParams.notification_template);
                }

                var notificationTemplateId = $stateParams.notification_template_id;

                var url = getBasePath('notification_templates') + notificationTemplateId + '/';
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
        label: '{{notification_obj.name}}'
    }
};
