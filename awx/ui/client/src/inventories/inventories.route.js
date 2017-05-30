import {templateUrl} from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';

export default {
    name: 'inventories', // top-most node in the generated tree (will replace this state definition)
    route: '/inventories',
    ncyBreadcrumb: {
        label: N_('INVENTORIES')
    },
    views: {
        '@': {
            templateUrl: templateUrl('inventories/inventories')
        },
        'list@inventories': {
            templateProvider: function(InventoryList, generateList) {
                let html = generateList.build({
                    list: InventoryList,
                    mode: 'edit'
                });
                return html;
            },
            controller: 'InventoryListController'
        }
    },
    searchPrefix: 'inventory',
    resolve: {
        Dataset: ['InventoryList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        canAdd: ['rbacUiControlService', function(rbacUiControlService) {
            return rbacUiControlService.canAdd('inventory')
                .then(function(res) {
                    return res.canAdd;
                })
                .catch(function() {
                    return false;
                });
        }]
    }
};
