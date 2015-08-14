/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'userPermissionsList',
    route: '/users/:user_id/permissions',
    templateUrl: templateUrl('permissions/user-permissions'),
    controller: 'permissionsListController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
