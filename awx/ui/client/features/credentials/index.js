import PermissionsList from '../../src/access/permissions-list.controller';
import CredentialForm from '../../src/credentials/credentials.form';
import CredentialList from '../../src/credentials/credentials.list';
import ListController from '../../src/credentials/list/credentials-list.controller';
import AddController from './add-credentials.controller.js';
import EditController from './edit-credentials.controller.js';
import {N_} from '../../src/i18n';

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
            ListDefinition: ['CredentialList', CredentialList => CredentialList],
            Dataset: [
                'CredentialList',
                'QuerySet',
                '$stateParams',
                'GetBasePath',
                '$interpolate',
                '$rootScope',
                '$state',
                (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope, $state) => {
                    list.basePath = 'api/v2/credentials/2/access_list/';
                    // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                    let path, interpolator;
                    if (GetBasePath(list.basePath)) {
                        path = GetBasePath(list.basePath);
                    } else {
                        interpolator = $interpolate(list.basePath);
                        path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                    }

                    $stateParams[`${list.iterator}_search`].order_by = 'username';
                    return qs.search(path, $stateParams[`${list.iterator}_search`]);

                }
            ]
        },
        params: {
            permission_search: {
                value: {
                    page_size: 20,
                    order_by: 'username'
                },
                dynamic: true,
                squash: ""
            }
        },
        ncyBreadcrumb: {
            parent: "credentials.edit",
            label: "PERMISSIONS"
        },
        views: {
            'permissions': {
                controller: PermissionsList,
                templateProvider: function(CredentialForm, CredentialList, GenerateForm) {
                    let form = CredentialForm;
                    let list = CredentialList;

                    let html = GenerateForm.buildCollection({
                        mode: 'edit',
                        related: 'permissions',
                        form: typeof(form) === 'function' ?  form() : form
                    });

                    return html;
                }
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
