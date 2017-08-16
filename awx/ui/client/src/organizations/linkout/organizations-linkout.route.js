/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import OrganizationsAdmins from './controllers/organizations-admins.controller';
import OrganizationsInventories from './controllers/organizations-inventories.controller';
import OrganizationsJobTemplates from './controllers/organizations-job-templates.controller';
import OrganizationsProjects from './controllers/organizations-projects.controller';
import OrganizationsTeams from './controllers/organizations-teams.controller';
import OrganizationsUsers from './controllers/organizations-users.controller';
import { N_ } from '../../i18n';

export default [{
    name: 'organizations.users',
    url: '/:organization_id/users',
    searchPrefix: 'user',
    views: {
        'form': {
            controller: OrganizationsUsers,
            templateProvider: function(OrgUserList, generateList) {
                let html = generateList.build({
                    list: OrgUserList,
                    mode: 'edit',
                    cancelButton: true
                });
                return generateList.wrapPanel(html);
            },
        }
    },
    params: {
        user_search: {
            value: {
                order_by: 'username'
            },
            dynamic: true
        }
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: N_("USERS")
    },

    data: {
        activityStream: true,
        activityStreamTarget: 'organization'
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgUsersDataset: ['OrgUserList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams.user_search);
            }
        ],
        OrgUserList: ['UserList', 'GetBasePath', '$stateParams', function(UserList, GetBasePath, $stateParams) {
            let list = _.cloneDeep(UserList);
            delete list.actions.add;
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/users`;
            list.searchRowActions = {
                add: {
                    buttonContent: '&#43; ADD user',
                    awToolTip: 'Add existing user to organization',
                    actionClass: 'btn List-buttonSubmit',
                    ngClick: 'addUsers()'
                }
            };
            return list;
        }]
    }
}, {
    name: 'organizations.teams',
    url: '/:organization_id/teams',
    searchPrefix: 'team',
    views: {
        'form': {
            controller: OrganizationsTeams,
            templateProvider: function(OrgTeamList, generateList) {
                let html = generateList.build({
                    list: OrgTeamList,
                    mode: 'edit',
                    cancelButton: true
                });
                return generateList.wrapPanel(html);
            },
        },
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'organization'
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: N_("TEAMS")
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgTeamList: ['TeamList', 'GetBasePath', '$stateParams', function(TeamList, GetBasePath, $stateParams) {
            let list = _.cloneDeep(TeamList);
            delete list.actions.add;
            // @issue Why is the delete action unavailable in this view?
            delete list.fieldActions.delete;
            list.listTitle = N_('Teams') + ` | {{ name }}`;
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/teams`;
            list.emptyListText = "This list is populated by teams added from the&nbsp;<a ui-sref='teams.add'>Teams</a>&nbsp;section";
            return list;
        }],
        OrgTeamsDataset: ['OrgTeamList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams.team_search);
            }
        ]
    }
}, {
    name: 'organizations.inventories',
    url: '/:organization_id/inventories',
    searchPrefix: 'inventory',
    views: {
        'form': {
            controller: OrganizationsInventories,
            templateProvider: function(OrgInventoryList, generateList) {
                let html = generateList.build({
                    list: OrgInventoryList,
                    mode: 'edit',
                    cancelButton: true
                });
                return generateList.wrapPanel(html);
            },
        },
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'organization'
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: N_("INVENTORIES")
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgInventoryList: ['InventoryList', 'GetBasePath', '$stateParams', function(InventoryList, GetBasePath, $stateParams) {
            let list = _.cloneDeep(InventoryList);
            delete list.actions.add;
            // @issue Why is the delete action unavailable in this view?
            delete list.fieldActions.delete;
            list.title = true;
            list.listTitle = N_('Inventories') + ` | {{ name }}`;
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/inventories`;
            list.emptyListText = "This list is populated by inventories added from the&nbsp;<a ui-sref='inventories.add'>Inventories</a>&nbsp;section";
            return list;
        }],
        OrgInventoryDataset: ['OrgInventoryList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams.inventory_search);
            }
        ]
    }
}, {
    name: 'organizations.projects',
    url: '/:organization_id/projects',
    searchPrefix: 'project',
    views: {
        'form': {
            controller: OrganizationsProjects,
            templateProvider: function(OrgProjectList, generateList) {
                let html = generateList.build({
                    list: OrgProjectList,
                    mode: 'edit',
                    cancelButton: true
                });
                return generateList.wrapPanel(html);
            },
        },
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'organization',
        socket: {
            "groups": {
                "jobs": ["status_changed"]
            }
        },
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: N_("PROJECTS")
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgProjectList: ['ProjectList', 'GetBasePath', '$stateParams', function(ProjectList, GetBasePath, $stateParams) {
            let list = _.cloneDeep(ProjectList);
            delete list.actions;
            // @issue Why is the delete action unavailable in this view?
            delete list.fieldActions.delete;
            list.listTitle = N_('Projects') + ` | {{ name }}`;
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/projects`;
            list.emptyListText = "This list is populated by projects added from the&nbsp;<a ui-sref='projects.add'>Projects</a>&nbsp;section";
            return list;
        }],
        OrgProjectDataset: ['OrgProjectList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams.project_search);
            }
        ]
    }
}, {
    name: 'organizations.job_templates',
    url: '/:organization_id/job_templates',
    searchPrefix: 'job_template',
    views: {
        'form': {
            controller: OrganizationsJobTemplates,
            templateProvider: function(OrgJobTemplateList, generateList) {
                let html = generateList.build({
                    list: OrgJobTemplateList,
                    mode: 'edit',
                    cancelButton: true
                });
                return generateList.wrapPanel(html);
            },
        },
    },
    params: {
        template_search: {
            value: {
                or__project__organization: null,
                or__inventory__organization: null,
                page_size: 20
            },
            dynamic: true
        }
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'organization',
        socket: {
            "groups": {
                "jobs": ["status_changed"]
            }
        }
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: N_("JOB TEMPLATES")
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgJobTemplateList: ['TemplateList', 'GetBasePath', '$stateParams', function(TemplateList) {
            let list = _.cloneDeep(TemplateList);
            delete list.actions;
            // @issue Why is the delete action unavailable in this view?
            delete list.fieldActions.delete;
            delete list.fields.type;
            list.listTitle = N_('Job Templates') + ` | {{ name }}`;
            list.emptyListText = "This list is populated by job templates added from the&nbsp;<a ui-sref='templates.addJobTemplate'>Job Templates</a>&nbsp;section";
            list.iterator = 'template';
            list.name = 'job_templates';
            list.basePath = "job_templates";
            list.fields.smart_status.ngInclude = "'/static/partials/organizations-job-template-smart-status.html'";
            list.fields.name.ngHref = '#/templates/job_template/{{template.id}}';
            list.fieldActions.submit.ngClick = 'submitJob(template.id)';
            list.fieldActions.schedule.ngClick = 'scheduleJob(template.id)';
            list.fieldActions.copy.ngClick = 'copyTemplate(template.id)';
            list.fieldActions.edit.ngClick = "editJobTemplate(template.id)";
            list.fieldActions.view.ngClick = "editJobTemplate(template.id)";
            return list;
        }],
        OrgJobTemplateDataset: ['OrgJobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.name);
                $stateParams.template_search.or__project__organization = $stateParams.organization_id;
                $stateParams.template_search.or__inventory__organization = $stateParams.organization_id;
                return qs.search(path, $stateParams.template_search);
            }
        ]
    }
}, {
    name: 'organizations.admins',
    url: '/:organization_id/admins',
    searchPrefix: 'user',
    params: {
        user_search: {
            value: {
                order_by: 'username'
            },
            dynamic: true
        },
        add_user_search: {
            value: {
                order_by: 'username',
                page_size: '5',
            },
            dynamic: true,
            squash: true
        }
    },
    views: {
        'form': {
            controller: OrganizationsAdmins,
            templateProvider: function(OrgAdminList, generateList) {
                let html = generateList.build({
                    list: OrgAdminList,
                    mode: 'edit',
                    cancelButton: true
                });
                return generateList.wrapPanel(html);
            },
        }
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'organization'
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: N_("ADMINS")
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgAdminsDataset: ['OrgAdminList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams[`user_search`]);
            }
        ],
        OrgAdminList: ['UserList', 'GetBasePath', '$stateParams', function(UserList, GetBasePath, $stateParams) {
            let list = _.cloneDeep(UserList);
            delete list.actions.add;
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/admins`;
            list.searchRowActions = {
                add: {
                    buttonContent: '&#43; ADD administrator',
                    awToolTip: 'Add existing user to organization as administrator',
                    actionClass: 'btn List-buttonSubmit',
                    ngClick: 'addUsers()'
                }
            };
            list.listTitle = N_('Admins') + ` | {{ name }}`;
            return list;
        }]
    }
}];
