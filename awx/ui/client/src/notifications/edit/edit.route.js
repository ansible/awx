/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'notifications.edit',
    route: '/edit',
    templateUrl: templateUrl('notifications/edit/edit'),
    controller: 'notificationsEditController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    },
    ncyBreadcrumb: {
        parent: 'notifications',
        label: 'Edit Notification'
    }
};
