import ListController from '../../src/credentials/list/credentials-list.controller';
import { N_ } from '../../src/i18n';

const indexTemplate = require('~features/credentials/index.view.html');

function LegacyCredentialsService () {
    this.list = {
        name: 'credentials',
        route: '/credentials',
        ncyBreadcrumb: {
            label: N_('CREDENTIALS')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'credential'
        },
        views: {
            '@': {
                templateUrl: indexTemplate
            },
            'list@credentials': {
                templateProvider (CredentialList, generateList) {
                    const html = generateList.build({
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
                (list, qs, $stateParams, GetBasePath) => {
                    const path = GetBasePath(list.basePath) || GetBasePath(list.name);

                    return qs.search(path, $stateParams[`${list.iterator}_search`]);
                }
            ],
            credentialType: ['CredentialTypeModel', CredentialType => new CredentialType('get')]
        }
    };

    this.editPermissions = {
        name: 'credentials.edit.permissions',
        url: '/permissions?{permission_search:queryset}',
        resolve: {
            ListDefinition: () => ({
                name: 'permissions',
                disabled: 'organization === undefined',
                ngClick: 'organization === undefined || $state.go(\'credentials.edit.permissions\')',
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
                        ngClick: '$state.go(\'.add\')',
                        label: N_('Add'),
                        awToolTip: N_('Add a permission'),
                        actionClass: 'at-Button--add',
                        actionId: 'button-add--permission',
                        ngShow: '(credential_obj.summary_fields.user_capabilities.edit || canAdd)'
                    }
                },
                fields: {
                    username: {
                        key: true,
                        label: N_('User'),
                        linkBase: 'users',
                        columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-4'
                    },
                    role: {
                        label: N_('Role'),
                        type: 'role',
                        nosort: true,
                        columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-4'
                    },
                    team_roles: {
                        label: N_('Team Roles'),
                        type: 'team_roles',
                        nosort: true,
                        columnClass: 'col-lg-5 col-md-5 col-sm-5 col-xs-4'
                    }
                }
            }),
            Dataset: ['QuerySet', '$stateParams', (qs, $stateParams) => {
                const id = $stateParams.credential_id;
                const path = `api/v2/credentials/${id}/access_list/`;

                return qs.search(path, $stateParams.permission_search);
            }]
        },
        params: {
            permission_search: {
                value: {
                    page_size: '20',
                    order_by: 'username'
                },
                dynamic: true,
                squash: ''
            }
        },
        ncyBreadcrumb: {
            parent: 'credentials.edit',
            label: N_('PERMISSIONS')
        },
        views: {
            related: {
                templateProvider (CredentialForm, GenerateForm) {
                    const html = GenerateForm.buildCollection({
                        mode: 'edit',
                        related: 'permissions',
                        form: typeof (CredentialForm) === 'function' ?
                            CredentialForm() : CredentialForm
                    });
                    return html;
                },
                controller: 'PermissionsList'
            }
        }
    };

    this.addPermissions = {
        name: 'credentials.edit.permissions.add',
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
            resourceData: ['CredentialModel', '$stateParams', (Credential, $stateParams) =>
                new Credential('get', $stateParams.credential_id)
                    .then(credential => ({ data: credential.get() }))
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
            'modal@credentials.edit': {
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
    };

    this.lookupTemplateProvider = (ListDefinition, generateList) => {
        const html = generateList.build({
            mode: 'lookup',
            list: ListDefinition,
            input_type: 'radio'
        });

        return `<lookup-modal>${html}</lookup-modal>`;
    };

    this.organization = {
        url: '/organization?selected',
        searchPrefix: 'organization',
        params: {
            organization_search: {
                value: {
                    page_size: 5,
                    order_by: 'name',
                    role_level: 'credential_admin_role'
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
        views: {},
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
    };

    this.credentialType = {
        url: '/credential_type?selected',
        searchPrefix: 'credential_type',
        params: {
            credential_type_search: {
                value: {
                    page_size: 5,
                    order_by: 'name'
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'credential_types',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {},
        resolve: {
            ListDefinition: ['CredentialTypesList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => qs.search(
                    GetBasePath('credential_types'),
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
    };

    this.getStateConfiguration = (name) => {
        switch (name) {
            case 'list':
                return this.list;
            case 'edit-permissions':
                return this.editPermissions;
            case 'add-permissions':
                return this.addPermissions;
            case 'add-organization':
                this.organization.name = 'credentials.add.organization';
                this.organization.views['organization@credentials.add'] = {
                    templateProvider: this.lookupTemplateProvider
                };

                return this.organization;
            case 'edit-organization':
                this.organization.name = 'credentials.edit.organization';
                this.organization.views['organization@credentials.edit'] = {
                    templateProvider: this.lookupTemplateProvider
                };

                return this.organization;
            case 'add-credential-type':
                this.credentialType.name = 'credentials.add.credentialType';
                this.credentialType.views['credential_type@credentials.add'] = {
                    templateProvider: this.lookupTemplateProvider
                };

                return this.credentialType;
            case 'edit-credential-type':
                this.credentialType.name = 'credentials.edit.credentialType';
                this.credentialType.views['credential_type@credentials.edit'] = {
                    templateProvider: this.lookupTemplateProvider
                };

                return this.credentialType;

            default:
                throw new Error(N_(`Legacy state configuration for ${name} does not exist`));
        }
    };
}

export default LegacyCredentialsService;
