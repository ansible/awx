import { N_ } from '../../i18n';

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
            templateProvider: function(RelatedHostsListDefinition, generateList, $stateParams, GetBasePath) {
                let list = _.cloneDeep(RelatedHostsListDefinition);
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
        Dataset: ['RelatedHostsListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
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
        hostsUrl: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return $stateParams.group && $stateParams.group.length > 0 ?
                // nested context - provide all hosts managed by nodes
                InventoryManageService.childHostsUrl(_.last($stateParams.group)) :
                // root context - provide all hosts in an inventory
                InventoryManageService.rootHostsUrl($stateParams.inventory_id);
        }],
        hostsDataset: ['RelatedHostsListDefinition', 'QuerySet', '$stateParams', 'hostsUrl', (list, qs, $stateParams, hostsUrl) => {
            let path = hostsUrl;
            return qs.search(path, $stateParams[`${list.iterator}_search`]);
        }],
        inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
        }]
    }
};
