import {templateUrl} from '../../shared/template-url/template-url.factory';
import { N_ } from '../../i18n';

export default {
    name: 'inventories', // top-most node in the generated tree (will replace this state definition)
    route: '/inventories',
    ncyBreadcrumb: {
        label: N_('INVENTORIES')
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'inventory',
        socket: {
            "groups": {
                inventories: ["status_changed"]
            }
        }
    },
    views: {
        '@': {
            templateUrl: templateUrl('inventories-hosts/inventories/inventories')
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
        }],
        InstanceGroupsData: ['Rest', 'GetBasePath', 'ProcessErrors', (Rest, GetBasePath, ProcessErrors) => {
                const url = GetBasePath('instance_groups');
                Rest.setUrl(url);
                return Rest.get()
                    .then(({data}) => {
                        return data.results.map((i) => ({name: i.name, id: i.id}));
                    })
                    .catch(({data, status}) => {
                    ProcessErrors(null, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to get instance groups info. GET returned status: ' + status
                    });
                });
        }]
    }
};
