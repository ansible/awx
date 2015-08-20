/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'teamPermissionsEdit',
    route: '/teams/:team_id/permissions/:permission_id',
    templateUrl: templateUrl('permissions/shared/team-permissions'),
    controller: 'editController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
