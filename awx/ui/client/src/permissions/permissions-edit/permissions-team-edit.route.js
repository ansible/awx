/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'teamPermissionsEdit',
    route: '/teams/:team_id/permissions/edit',
    templateUrl: templateUrl('permissions/team-permissions'),
    controller: 'editController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
