/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'activityStream',
    route: '/activity_stream?target&id',
    templateUrl: templateUrl('activity-stream/activitystream'),
    controller: 'activityStreamController',
    ncyBreadcrumb: {
        label: "ACTIVITY STREAM"
    },
};
