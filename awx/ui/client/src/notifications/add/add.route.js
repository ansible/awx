/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'notifications.add',
    route: '/add',
    templateUrl: templateUrl('notifications/add/add'),
    controller: 'notificationsAddController',
    ncyBreadcrumb: {
        parent: 'notifications',
        label: 'Create Notification Template'
    }
};
