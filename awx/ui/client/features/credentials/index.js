import PermissionsList from '../../src/access/permissions-list.controller';
import CredentialForm from '../../src/credentials/credentials.form';
import CredentialList from '../../src/credentials/credentials.list';
import ListController from '../../src/credentials/list/credentials-list.controller';
import AddController from './add-credentials.controller.js';
import EditController from './edit-credentials.controller.js';
import { N_ } from '../../src/i18n';

function CredentialsResolve ($q, $stateParams, Me, Credential, CredentialType) {
    let id = $stateParams.credential_id;

    let promises = {
        me: new Me('get'),
        credentialType: new CredentialType('get')
    };

    if (id) {
        promises.credential = new Credential(['get', 'options'], [id, id]);
    } else {
        promises.credential = new Credential('options');
    }

    return $q.all(promises);
}

CredentialsResolve.$inject = [
    '$q',
    '$stateParams',
    'MeModel',
    'CredentialModel',
    'CredentialTypeModel'
];

function CredentialsConfig ($stateProvider, $stateExtenderProvider, stateDefinitionsProvider, pathServiceProvider) {
    let pathService = pathServiceProvider.$get();
    let stateExtender = $stateExtenderProvider.$get();
    let stateDefinitions = stateDefinitionsProvider.$get();

    stateExtender.addState({
        name: 'credentials',
        route: '/credentials',
        ncyBreadcrumb: {
            label: N_('CREDENTIALS')
        },
        views: {
            '@': {
                templateUrl: pathService.getViewPath('credentials/index')
            },
            'list@credentials': {
                templateProvider: function(CredentialList, generateList) {
                    let html = generateList.build({
                        list: CredentialList,
                        mode: 'edit'
                    });

                    return html;
                },
                controller: ListController
            }
        },
        searchPrefix: 'credential',
        resolve: {
            Dataset: ['CredentialList', 'QuerySet', '$stateParams', 'GetBasePath',
                function(list, qs, $stateParams, GetBasePath) {
                    let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                    return qs.search(path, $stateParams[`${list.iterator}_search`]);
                }
            ]
        }
    });

    stateExtender.addState({
        name: 'credentials.add',
        route: '/add',
        ncyBreadcrumb: {
            label: N_('CREATE CREDENTIALS')
        },
        views: {
            'add@credentials': {
                templateUrl: pathService.getViewPath('credentials/add-edit-credentials'),
                controller: AddController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: CredentialsResolve
        }
    });

    stateExtender.addState({
        name: 'credentials.edit',
        route: '/:credential_id',
        ncyBreadcrumb: {
            label: N_('EDIT')
        },
        views: {
            'edit@credentials': {
                templateUrl: pathService.getViewPath('credentials/add-edit-credentials'),
                controller: EditController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: CredentialsResolve
        }
    });

    stateExtender.addState({
        name: "credentials.edit.permissions",
        url: "/permissions?{permission_search:queryset}",
        resolve: {
            ListDefinition: () => {
                return {
                    name: 'permissions',
                    disabled: '(organization === undefined ? true : false)',
                    // Do not transition the state if organization is undefined
                    ngClick: `(organization === undefined ? true : false)||$state.go('credentials.edit.permissions')`,
                    awToolTip: '{{permissionsTooltip}}',
                    dataTipWatch: 'permissionsTooltip',
                    awToolTipTabEnabledInEditMode: true,
                    dataPlacement: 'right',
                    basePath: 'api/v2/credentials/{{$stateParams.id}}/access_list/',
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
                            ngClick: "$state.go('.add')",
                            label: 'Add',
                            awToolTip: N_('Add a permission'),
                            actionClass: 'btn List-buttonSubmit',
                            buttonContent: '&#43; ' + N_('ADD'),
                            ngShow: '(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
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
                };
            },
            Dataset: ['QuerySet', '$stateParams', (qs, $stateParams) => {
                    let id = $stateParams.credential_id;
                    let path = `api/v2/credentials/${id}/access_list/`;

                    return qs.search(path, $stateParams[`permission_search`]);
                }
            ]
        },
        params: {
            permission_search: {
                value: {
                    page_size: "20",
                    order_by: "username"
                },
                dynamic:true,
                squash:""
            }
        },
        ncyBreadcrumb: {
            parent: "credentials.edit",
            label: "PERMISSIONS"
        },
        views: {
            'related': {
                templateProvider: function(CredentialForm, GenerateForm) {
                    let html = GenerateForm.buildCollection({
                        mode: 'edit',
                        related: `permissions`,
                        form: typeof(CredentialForm) === 'function' ?
                            CredentialForm() : CredentialForm
                    });
                    return html;
                },
                controller: 'PermissionsList'
            }
        }
    });

    stateExtender.addState({
        name: 'credentials.edit.permissions.add',
        url: '/add-permissions',
        resolve: {
            usersDataset: [
                'addPermissionsUsersList',
                'QuerySet',
                '$stateParams',
                'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => {
                    let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                    return qs.search(path, $stateParams.user_search);

                }
            ],
            teamsDataset: [
                'addPermissionsTeamsList',
                'QuerySet',
                '$stateParams',
                'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => {
                    let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                    return qs.search(path, $stateParams.team_search);
                }
            ],
            resourceData: ['CredentialModel', '$stateParams', (Credential, $stateParams) => {
                return new Credential('get', $stateParams.credential_id)
                    .then(credential => ({ data: credential.get() }));
            }],
        },
        params: {
            user_search: {
                value: {
                    order_by: 'username',
                    page_size: 5
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
            'modal@credentials.edit': {
                template: `
                    <add-rbac-resource
                        users-dataset="$resolve.usersDataset"
                        teams-dataset="$resolve.teamsDataset"
                        selected="allSelected"
                        resource-data="$resolve.resourceData"
                        title="Add Users / Teams">
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
}

CredentialsConfig.$inject = [
  '$stateProvider',
  '$stateExtenderProvider',
  'stateDefinitionsProvider',
  'PathServiceProvider'
];

angular
    .module('at.features.credentials', [])
    .config(CredentialsConfig)
    .controller('AddController', AddController)
    .controller('EditController', EditController);
