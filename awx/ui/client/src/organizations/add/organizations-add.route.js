/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import OrganizationsAdd from './organizations-add.controller';

export default {
    name: 'organizations.add',
    route: '/add',
    templateUrl: templateUrl('organizations/add/organizations-add'),
    controller: OrganizationsAdd,
    ncyBreadcrumb: {
        parent: "organizations",
        label: "CREATE ORGANIZATION"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
