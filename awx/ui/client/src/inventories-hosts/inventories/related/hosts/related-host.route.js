import { N_ } from '../../../../i18n';

export default {
    name: "inventories.edit.hosts",
    url: "/hosts?{host_search:queryset}",
    params: {
        host_search: {
            value: {
                page_size: "20",
                order_by: "name"
            },
            dynamic: true,
            squash:""
        }
    },
    ncyBreadcrumb: {
        parent: "inventories.edit",
        label: N_("HOSTS")
    },
    views: {
        'related': {
            templateProvider: function(ListDefinition, generateList, $stateParams, GetBasePath) {
                let list = _.cloneDeep(ListDefinition);
                if($stateParams && $stateParams.group) {
                    list.basePath = GetBasePath('groups') + _.last($stateParams.group) + '/all_hosts';
                }
                else {
                    //reaches here if the user is on the root level group
                    list.basePath = GetBasePath('inventory') + $stateParams.inventory_id + '/hosts';
                }
                let html = generateList.build({
                    list: list,
                    mode: 'edit'
                });
                return html;
            },
            controller: 'RelatedHostListController'
        }
    },
    resolve: {
        ListDefinition: ['RelatedHostsListDefinition', '$stateParams', 'GetBasePath', (RelatedHostsListDefinition, $stateParams, GetBasePath) => {
            let list = _.cloneDeep(RelatedHostsListDefinition);
            list.basePath = GetBasePath('inventory') + $stateParams.inventory_id + '/hosts';
            return list;
        }],
        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
            (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope) => {
                // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                let path, interpolator;
                if (GetBasePath(list.basePath)) {
                    path = GetBasePath(list.basePath);
                } else {
                    interpolator = $interpolate(list.basePath);
                    path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                }
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        hostsUrl: ['InventoriesService', '$stateParams', function(InventoriesService, $stateParams) {
            return $stateParams.group && $stateParams.group.length > 0 ?
                // nested context - provide all hosts managed by nodes
                InventoriesService.childHostsUrl(_.last($stateParams.group)) :
                // root context - provide all hosts in an inventory
                InventoriesService.rootHostsUrl($stateParams.inventory_id);
        }],
        hostsDataset: ['ListDefinition', 'QuerySet', '$stateParams', 'hostsUrl', (list, qs, $stateParams, hostsUrl) => {
            let path = hostsUrl;
            return qs.search(path, $stateParams[`${list.iterator}_search`]);
        }],
        inventoryData: ['InventoriesService', '$stateParams', function(InventoriesService, $stateParams) {
            return InventoriesService.getInventory($stateParams.inventory_id).then(res => res.data);
        }],
        canAdd: ['rbacUiControlService', function(rbacUiControlService) {
            return rbacUiControlService.canAdd('hosts')
                .then(function(res) {
                    return res.canAdd;
                })
                .catch(function() {
                    return false;
                });
        }]
    }
};
