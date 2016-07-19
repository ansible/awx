/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import notificationTemplatesList from './notification-templates-list/main';
import notificationsAdd from './add/main';
import notificationsEdit from './edit/main';

import list from './notificationTemplates.list';
import form from './notificationTemplates.form';
import notificationsList from './notifications.list';
import toggleNotification from './shared/toggle-notification.factory';
import notificationsListInit from './shared/notification-list-init.factory';
import typeChange from './shared/type-change.service';

export default
    angular.module('notifications', [
            notificationTemplatesList.name,
            notificationsAdd.name,
            notificationsEdit.name
        ])
        .factory('NotificationTemplatesList', list)
        .factory('NotificationsFormObject', form)
        .factory('NotificationsList', notificationsList)
        .factory('ToggleNotification', toggleNotification)
        .factory('NotificationsListInit', notificationsListInit)
        .service('NotificationsTypeChange', typeChange);
