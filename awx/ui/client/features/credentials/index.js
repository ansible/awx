import CredentialList from './credentials.list.js';
import ListController from './list/credentials-list.controller';
import AddController from './add-credentials.controller.js';
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

    function CredentialsResolve ($q, params, Me, Credential, CredentialType) {
        let models;
        let id = params.id;
        let promises = {
            me: new Me('get')
        };

        if (!id) {
            promises.credential = new Credential('options');
            promises.credentialType = new CredentialType('get');

            return $q.all(promises).then(models => models);
        }
        
        promises.credential = new Credential('get', id);

        return $q.all(promises)
            .then(_models_ => {
                models = _models_;

                return new CredentialType('get', models.credential.get('id'));
            })
            .then(credentialType => {
                models.credentialType = credentialType;

                return models;
            });
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
                templateUrl: pathService.getViewPath('credentials/add-credentials'),
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
                templateUrl: pathService.getViewPath('credentials/add-credentials'),
                controller: AddController,
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
    .factory('CredentialList', CredentialList)
    .controller('ListController', ListController)
    .controller('AddController', AddController);
