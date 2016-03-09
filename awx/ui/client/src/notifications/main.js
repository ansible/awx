/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import notificationsList from './list/main';
import notificationsAdd from './add/main';
import notificationsEdit from './edit/main';

import list from './notifications.list';
import form from './notifications.form';

export default
    angular.module('notifications', [
            notificationsList.name,
            notificationsAdd.name,
            notificationsEdit.name
        ])
        .factory('notificationsListObject', list)
        .factory('notificationsFormObject', form);
