/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import OrganizationsList from './organizations-list.controller';

export default {
    name: 'organizations',
    route: '/organizations',
    templateUrl: templateUrl('organizations/list/organizations-list'),
    controller: OrganizationsList,
    data: {
        activityStream: true,
        activityStreamTarget: 'organization'
    },
    ncyBreadcrumb: {
        parent: function($scope) {
            $scope.$parent.$emit("ReloadOrgListView");
            return "setup";
        },
        label: "ORGANIZATIONS"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
