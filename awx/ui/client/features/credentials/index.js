import CredentialList from '../../src/credentials/credentials.list';
import ListController from '../../src/credentials/list/credentials-list.controller';
import AddController from './add-credentials.controller.js';
import EditController from './edit-credentials.controller.js';
import { N_ } from '../../src/i18n';

function config ($stateExtenderProvider, pathServiceProvider) {
    let pathService = pathServiceProvider.$get();
    let stateExtender = $stateExtenderProvider.$get();

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

    function CredentialsResolve ($q, $stateParams, Me, Credential, CredentialType) {
        let id = $stateParams.id;

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
        route: '/edit/:id',
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
}

config.$inject = [
  '$stateExtenderProvider',
  'PathServiceProvider'
];

angular
    .module('at.features.credentials', [])
    .config(config)
    .controller('AddController', AddController)
    .controller('EditController', EditController);
