import CredentialList from './credentials.list.js';
import ListController from './list/credentials-list.controller';
import AddController from './add-credentials.controller.js';
import { N_ } from '../i18n';

function config ($stateExtenderProvider) {
    let stateExtender = $stateExtenderProvider.$get();

    stateExtender.addState({
        name: 'credentials',
        route: '/credentials',
        ncyBreadcrumb: {
            label: N_('CREDENTIALS')
        },
        views: {
            '@': {
                templateUrl: '/static/views/credentials/index.view.html',
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
            label: N_('ADD')
        },
        views: {
            'add@credentials': {
                templateUrl: '/static/views/credentials/add-credentials.view.html',
                controller: AddController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            credentialType: ['CredentialType', CredentialType => {
                return CredentialType.get().then(() => CredentialType);
            }]
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
  '$stateExtenderProvider'
];

angular
    .module('at.feature.credentials', [])
    .config(config)
    .factory('CredentialList', CredentialList)
    .controller('ListController', ListController)
    .controller('AddController', AddController);
