/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import OrganizationsLinkout from './organizations-linkout.controller';

export default [
    {
        name: 'organizations.users',
        route: '/:organization_id/users',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsLinkout,
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
    },
    {
        name: 'organizations.teams',
        route: '/:organization_id/teams',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsLinkout,
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
    },
    {
        name: 'organizations.inventories',
        route: '/:organization_id/inventories',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsLinkout,
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
    },
    {
        name: 'organizations.projects',
        route: '/:organization_id/projects',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsLinkout,
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
    },
    {
        name: 'organizations.job_templates',
        route: '/:organization_id/job_templates',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsLinkout,
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
    },
    {
        name: 'organizations.admins',
        route: '/:organization_id/admins',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsLinkout,
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
    }
];
