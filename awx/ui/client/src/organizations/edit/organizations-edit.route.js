/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {
    templateUrl
} from '../../shared/template-url/template-url.factory';
import OrganizationsEdit from './organizations-edit.controller';

export default {
    name: 'organizations.edit',
    route: '/:organization_id',
    templateUrl: templateUrl('organizations/add/organizations-add'),
    controller: OrganizationsEdit,
    data: {
        activityStreamId: 'organization_id'
    },
    ncyBreadcrumb: {
        parent: "organizations",
        label: "{{name}}"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
