/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'notifications',
    route: '/notifications',
    templateUrl: templateUrl('notifications/notification-templates-list/list'),
    controller: 'notificationTemplatesListController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
