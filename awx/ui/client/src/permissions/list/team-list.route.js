/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'teamPermissionsList',
    route: '/teams/:team_id/permissions',
    templateUrl: templateUrl('permissions/shared/team-permissions'),
    controller: 'permissionsListController'
};
