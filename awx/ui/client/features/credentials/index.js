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

    function credentialTypeResolve ($q, credentialModel, credentialTypeModel) {
        let promises = [
            credentialModel.options(),
            credentialTypeModel.get()
        ];

        return $q.all(promises)
            .then(() => ({
                credential: credentialModel,
                credentialType: credentialTypeModel
            }));
    }

    credentialTypeResolve.$inject = ['$q', 'CredentialModel', 'CredentialTypeModel'];

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
            credentialType: credentialTypeResolve
        }
    });

    stateExtender.addState({
        name: 'credentials.edit',
        route: '/edit',
        ncyBreadcrumb: {
            label: N_('EDIT')
        },
        views: {
            'edit@credentials': {
                templateProvider: function() {
                    return '<span>test-edit</span>';
                }
            }
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
