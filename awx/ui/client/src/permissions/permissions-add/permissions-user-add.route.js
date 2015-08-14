/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'userPermissionsAdd',
    route: '/users/:user_id/permissions/add',
    templateUrl: templateUrl('permissions/user-permissions'),
    controller: 'addController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
