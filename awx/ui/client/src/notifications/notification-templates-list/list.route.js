/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'notifications',
    route: '/notification_templates',
    templateUrl: templateUrl('notifications/notification-templates-list/list'),
    controller: 'notificationTemplatesListController',
    ncyBreadcrumb: {
        parent: 'setup',
        label: 'NOTIFICATION TEMPLATES'
    },
};
