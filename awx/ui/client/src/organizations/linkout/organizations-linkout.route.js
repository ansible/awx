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
        },
        'modalBody@': {
            templateProvider: function(AddUserList, generateList) {
                let html = generateList.build({
                    list: AddUserList,
                    mode: 'edit',
                    listTitle: false
                });
                return html;
            },
        }
    },
    params: {
        user_search: {
            value: {
                order_by: 'username'
            }
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
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: "USERS"
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
        AddUsersDataset: ['AddUserList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams.add_user_search);
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
            list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
            return list;
        }],
        AddUserList: ['UserList', function(UserList) {
            let list = _.cloneDeep(UserList);
            list.basePath = 'users';
            list.iterator = 'add_user';
            list.name = 'add_users';
            list.multiSelect = true;
            delete list.actions;
            delete list.fieldActions;
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
        label: "TEAMS"
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
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/teams`;
            list.emptyListText = "This list is populated by teams added from the&nbsp;<a ui-sref='teams.add'>Teams</a>&nbsp;section";
            list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
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
        'form@': {
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
        label: "INVENTORIES"
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
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/inventories`;
            list.emptyListText = "This list is populated by inventories added from the&nbsp;<a ui-sref='inventories.add'>Inventories</a>&nbsp;section";
            list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
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
        'form@': {
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
        label: "PROJECTS"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        OrgProjectList: ['ProjectList', 'GetBasePath', '$stateParams', function(InventoryList, GetBasePath, $stateParams) {
            let list = _.cloneDeep(InventoryList);
            delete list.actions;
            // @issue Why is the delete action unavailable in this view?
            delete list.fieldActions.delete;
            list.basePath = `${GetBasePath('organizations')}${$stateParams.organization_id}/projects`;
            list.emptyListText = "This list is populated by projects added from the&nbsp;<a ui-sref='projects.add'>Projects</a>&nbsp;section";
            list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
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
        job_template_search: {
            value: {
                project__organization: null
            }
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
        label: "JOB TEMPLATES"
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
            list.emptyListText = "This list is populated by job templates added from the&nbsp;<a ui-sref='jobTemplates.add'>Job Templates</a>&nbsp;section";
            list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
            list.iterator = 'job_template';
            list.name = 'job_templates';
            return list;
        }],
        OrgJobTemplateDataset: ['OrgJobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.name);
                $stateParams.job_template_search.project__organization = $stateParams.organization_id;
                return qs.search(path, $stateParams.job_template_search);
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
            }
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
        },
        'modalBody@': {
            templateProvider: function(AddAdminList, generateList) {
                let html = generateList.build({
                    list: AddAdminList,
                    mode: 'edit',
                    listTitle: false
                });
                return html;
            },
        }
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'organization'
    },
    ncyBreadcrumb: {
        parent: "organizations.edit",
        label: "ADMINS"
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
        AddAdminsDataset: ['AddAdminList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || list.basePath;
                return qs.search(path, $stateParams[`add_user_search`]);
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
            list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
            return list;
        }],
        AddAdminList: ['UserList', function(UserList) {
            let list = _.cloneDeep(UserList);
            list.basePath = 'users';
            list.iterator = 'add_user';
            list.name = 'add_users';
            list.multiSelect = true;
            delete list.actions;
            delete list.fieldActions;
            return list;
        }]
    }
}];
