
import AddController from './add-applications.controller';
import EditController from './edit-applications.controller';
import ListController from './list-applications.controller';
import UserListController from './list-applications-users.controller';
import ApplicationsStrings from './applications.strings';
import { N_ } from '../../src/i18n';

const MODULE_NAME = 'at.features.applications';

const addEditTemplate = require('~features/applications/add-edit-applications.view.html');
const listTemplate = require('~features/applications/list-applications.view.html');
const indexTemplate = require('~features/applications/index.view.html');
const userListTemplate = require('~features/applications/list-applications-users.view.html');

function ApplicationsDetailResolve ($q, $stateParams, Me, Application, Organization) {
    const id = $stateParams.application_id;

    const promises = {
        me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
    };

    if (!id) {
        promises.application = new Application('options');
        promises.organization = new Organization();

        return $q.all(promises);
    }

    promises.application = new Application(['get', 'options'], [id, id]);

    return $q.all(promises)
        .then(models => {
            const orgId = models.application.get('organization');

            const dependents = {
                organization: new Organization('get', orgId)
            };

            return $q.all(dependents)
                .then(related => {
                    models.organization = related.organization;

                    return models;
                });
        });
}

ApplicationsDetailResolve.$inject = [
    '$q',
    '$stateParams',
    'MeModel',
    'ApplicationModel',
    'OrganizationModel'
];

function ApplicationsRun ($stateExtender, strings) {
    $stateExtender.addState({
        name: 'applications',
        route: '/applications',
        ncyBreadcrumb: {
            label: strings.get('state.LIST_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            // TODO: double-check activity stream works
            activityStreamTarget: 'application'
        },
        views: {
            '@': {
                templateUrl: indexTemplate,
            },
            'list@applications': {
                templateUrl: listTemplate,
                controller: ListController,
                controllerAs: 'vm'
            }
        },
        searchPrefix: 'application',
        resolve: {
            resolvedModels: [
                'ApplicationModel',
                (Application) => {
                    const app = new Application(['options']);
                    return app;
                }
            ],
            Dataset: [
                '$stateParams',
                'Wait',
                'GetBasePath',
                'QuerySet',
                ($stateParams, Wait, GetBasePath, qs) => {
                    const searchParam = $stateParams.application_search;
                    const searchPath = GetBasePath('applications');

                    Wait('start');
                    return qs.search(searchPath, searchParam)
                        .finally(() => {
                            Wait('stop');
                        });
                }
            ],
        }
    });

    $stateExtender.addState({
        name: 'applications.add',
        route: '/add',
        ncyBreadcrumb: {
            label: strings.get('state.ADD_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            // TODO: double-check activity stream works
            activityStreamTarget: 'application'
        },
        views: {
            'add@applications': {
                templateUrl: addEditTemplate,
                controller: AddController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: ApplicationsDetailResolve
        }
    });

    $stateExtender.addState({
        name: 'applications.edit',
        route: '/:application_id',
        ncyBreadcrumb: {
            label: strings.get('state.EDIT_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'application',
            activityStreamId: 'application_id'
        },
        views: {
            'edit@applications': {
                templateUrl: addEditTemplate,
                controller: EditController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: ApplicationsDetailResolve
        }
    });

    $stateExtender.addState({
        name: 'applications.add.organization',
        url: '/organization?selected',
        searchPrefix: 'organization',
        params: {
            organization_search: {
                value: {
                    page_size: 5,
                    order_by: 'name',
                    role_level: 'admin_role'
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'organizations',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'organization@applications.add': {
                templateProvider: (ListDefinition, generateList) => {
                    const html = generateList.build({
                        mode: 'lookup',
                        list: ListDefinition,
                        input_type: 'radio'
                    });

                    return `<lookup-modal>${html}</lookup-modal>`;
                }
            }
        },
        resolve: {
            ListDefinition: ['OrganizationList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => qs.search(
                    GetBasePath('organizations'),
                    $stateParams[`${list.iterator}_search`]
                )
            ]
        },
        onExit ($state) {
            if ($state.transition) {
                $('#form-modal').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        }
    });

    $stateExtender.addState({
        name: 'applications.edit.permissions',
        route: '/permissions?{permission_search:queryset}',
        ncyBreadcrumb: {
            label: strings.get('state.PERMISSIONS_BREADCRUMB_LABEL'),
            parent: 'applications.edit'
        },
        params: {
            permission_search: {
                dynamic: true,
                squash: '',
                value: {
                    page_size: '20',
                    order_by: 'username'
                }
            }
        },
        resolve: {
            Dataset: ['QuerySet', '$stateParams', (qs, $stateParams) => {
                const id = $stateParams.application_id;
                // TODO: no access_list endpoint given by api
                const path = `api/v2/applications/${id}/access_list/`;

                return qs.search(path, $stateParams.permission_search);
            }],
            ListDefinition: () => ({
                name: 'permissions',
                disabled: 'organization === undefined',
                ngClick: 'organization === undefined || $state.go(\'applications.edit.permissions\')',
                awToolTip: '{{permissionsTooltip}}',
                dataTipWatch: 'permissionsTooltip',
                awToolTipTabEnabledInEditMode: true,
                dataPlacement: 'right',
                basePath: 'api/v2/applications/{{$stateParams.id}}/access_list/',
                search: {
                    order_by: 'username'
                },
                type: 'collection',
                title: N_('Permissions'),
                iterator: 'permission',
                index: false,
                open: false,
                actions: {
                    add: {
                        ngClick: '$state.go(\'.add\')',
                        label: 'Add',
                        awToolTip: N_('Add a permission'),
                        actionClass: 'btn List-buttonSubmit',
                        buttonContent: `&#43; ${N_('ADD')}`,
                        ngShow: '(application_obj.summary_fields.user_capabilities.edit || canAdd)'
                    }
                },
                fields: {
                    username: {
                        key: true,
                        label: N_('User'),
                        linkBase: 'users',
                        class: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                    },
                    role: {
                        label: N_('Role'),
                        type: 'role',
                        nosort: true,
                        class: 'col-lg-4 col-md-4 col-sm-4 col-xs-4'
                    },
                    team_roles: {
                        label: N_('Team Roles'),
                        type: 'team_roles',
                        nosort: true,
                        class: 'col-lg-5 col-md-5 col-sm-5 col-xs-4'
                    }
                }
            }),
        }
    });

    $stateExtender.addState({
        name: 'applications.edit.permissions.add',
        url: '/add-permissions',
        resolve: {
            usersDataset: [
                'addPermissionsUsersList',
                'QuerySet',
                '$stateParams',
                'GetBasePath',
                'resourceData',
                (list, qs, $stateParams, GetBasePath, resourceData) => {
                    let path;

                    if (resourceData.data.organization) {
                        path = `${GetBasePath('organizations')}${resourceData.data.organization}/users`;
                    } else {
                        path = list.basePath || GetBasePath(list.name);
                    }

                    return qs.search(path, $stateParams.user_search);
                }
            ],
            teamsDataset: [
                'addPermissionsTeamsList',
                'QuerySet',
                '$stateParams',
                'GetBasePath',
                'resourceData',
                (list, qs, $stateParams, GetBasePath, resourceData) => {
                    const path = GetBasePath(list.basePath) || GetBasePath(list.name);
                    const org = resourceData.data.organization;

                    if (!org) {
                        return null;
                    }

                    $stateParams[`${list.iterator}_search`].organization = org;

                    return qs.search(path, $stateParams.team_search);
                }
            ],
            resourceData: ['ApplicationModel', '$stateParams', (Application, $stateParams) =>
                new Application('get', $stateParams.application_id)
                    .then(application => ({ data: application.get() }))
            ]
        },
        params: {
            user_search: {
                value: {
                    order_by: 'username',
                    page_size: 5,
                    is_superuser: false
                },
                dynamic: true
            },
            team_search: {
                value: {
                    order_by: 'name',
                    page_size: 5
                },
                dynamic: true
            }
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'modal@applications.edit': {
                template: `
                    <add-rbac-resource
                        users-dataset='$resolve.usersDataset'
                        teams-dataset='$resolve.teamsDataset'
                        selected='allSelected'
                        resource-data='$resolve.resourceData'
                        without-team-permissions='{{$resolve.resourceData.data.organization ? null : true}}'
                        title='{{$resolve.resourceData.data.organization ? "Add Users / Teams" : "Add Users"}}'>
                    </add-rbac-resource>`
            }
        },
        onExit: $state => {
            if ($state.transition) {
                $('#add-permissions-modal').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        }
    });

    $stateExtender.addState({
        name: 'applications.edit.users',
        route: '/users',
        ncyBreadcrumb: {
            label: strings.get('state.USER_LIST_BREADCRUMB_LABEL'),
            parent: 'applications.edit'
        },
        data: {
            activityStream: true,
            // TODO: double-check activity stream works
            activityStreamTarget: 'application'
        },
        views: {
            'userList@applications.edit': {
                templateUrl: userListTemplate,
                controller: UserListController,
                controllerAs: 'vm'
            }
        },
        params: {
            user_search: {
                value: {
                    order_by: 'user',
                    page_size: 20
                },
                dynamic: true
            }
        },
        searchPrefix: 'user',
        resolve: {
            resolvedModels: [
                'ApplicationModel',
                (Application) => {
                    const app = new Application(['options']);
                    return app;
                }
            ],
            Dataset: [
                '$stateParams',
                'Wait',
                'GetBasePath',
                'QuerySet',
                ($stateParams, Wait, GetBasePath, qs) => {
                    const searchParam = $stateParams.user_search;
                    const searchPath = `${GetBasePath('applications')}${$stateParams.application_id}/tokens`;

                    Wait('start');
                    return qs.search(searchPath, searchParam)
                        .finally(() => {
                            Wait('stop');
                        });
                }
            ],
        }
    });
}

ApplicationsRun.$inject = [
    '$stateExtender',
    'ApplicationsStrings'
];

angular
    .module(MODULE_NAME, [])
    .service('ApplicationsStrings', ApplicationsStrings)
    .run(ApplicationsRun);

export default MODULE_NAME;
