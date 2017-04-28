import CredentialList from './credentials.list.js';
import ListController from './list/credentials-list.controller';
import { N_ } from '../i18n';

function routes ($stateExtenderProvider) {
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
                templateProvider: function() {
                    return '<span>test-add</span>';
                }
            }
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

routes.$inject = [
  '$stateExtenderProvider'
];

angular
    .module('at.feature.credentials', [])
    .config(routes)
    .factory('CredentialList', CredentialList)
    .controller('ListController', ListController);
