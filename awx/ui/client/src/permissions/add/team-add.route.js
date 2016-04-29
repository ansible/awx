/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'teamPermissionsAdd',
    route: '/teams/:team_id/permissions/add',
    templateUrl: templateUrl('permissions/shared/team-permissions'),
    controller: 'permissionsAddController'
};
