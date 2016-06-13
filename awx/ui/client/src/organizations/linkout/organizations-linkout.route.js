/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import OrganizationsAdmins from './controllers/organizations-admins.controller';
import OrganizationsInventories from './controllers/organizations-inventories.controller';
import OrganizationsJobTemplates from './controllers/organizations-job-templates.controller';
import OrganizationsProjects from './controllers/organizations-projects.controller';
import OrganizationsTeams from './controllers/organizations-teams.controller';
import OrganizationsUsers from './controllers/organizations-users.controller';

export default [
    {
        name: 'organizations.users',
        route: '/:organization_id/users',
        templateUrl: templateUrl('organizations/linkout/organizations-linkout'),
        controller: OrganizationsUsers,
        data: {
            activityStream: true,
            activityStreamTarget: 'organization'
        },
        ncyBreadcrumb: {
            parent: function($scope) {
                $scope.$parent.$emit("ReloadOrgListView");
                return "organizations.edit";
            },
            label: "USERS"
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
        controller: OrganizationsTeams,
        data: {
            activityStream: true,
            activityStreamTarget: 'organization'
        },
        ncyBreadcrumb: {
            parent: function($scope) {
                $scope.$parent.$emit("ReloadOrgListView");
                return "organizations.edit";
            },
            label: "TEAMS"
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
        controller: OrganizationsInventories,
        data: {
            activityStream: true,
            activityStreamTarget: 'organization'
        },
        ncyBreadcrumb: {
            parent: function($scope) {
                $scope.$parent.$emit("ReloadOrgListView");
                return "organizations.edit";
            },
            label: "INVENTORIES"
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
        controller: OrganizationsProjects,
        data: {
            activityStream: true,
            activityStreamTarget: 'organization'
        },
        ncyBreadcrumb: {
            parent: function($scope) {
                $scope.$parent.$emit("ReloadOrgListView");
                return "organizations.edit";
            },
            label: "PROJECTS"
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
        controller: OrganizationsJobTemplates,
        data: {
            activityStream: true,
            activityStreamTarget: 'organization'
        },
        ncyBreadcrumb: {
            parent: function($scope) {
                $scope.$parent.$emit("ReloadOrgListView");
                return "organizations.edit";
            },
            label: "JOB TEMPLATES"
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
        controller: OrganizationsAdmins,
        data: {
            activityStream: true,
            activityStreamTarget: 'organization'
        },
        ncyBreadcrumb: {
            parent: function($scope) {
                $scope.$parent.$emit("ReloadOrgListView");
                return "organizations.edit";
            },
            label: "ADMINS"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    }
];
