import { N_ } from '../../../i18n';

export default {
    name: "inventories.edit.groups.edit.nested_hosts",
    url: "/nested_hosts?{nested_host_search:queryset}",
    params: {
        nested_host_search: {
            value: {
                page_size: "20",
                order_by: "name"
            },
            dynamic: true,
            squash: ""
        }
    },
    ncyBreadcrumb: {
        parent: "inventories.edit.groups.edit",
        label: N_("ASSOCIATED HOSTS")
    },
    views: {
        // 'related@inventories.edit.groups.edit': {
        'related': {
            templateProvider: function(NestedHostsListDefinition, generateList) {
                let list = _.cloneDeep(NestedHostsListDefinition);

                let html = generateList.build({
                    list: list,
                    mode: 'edit'
                });
                // Include the custom group delete modal template
                // return $templateRequest(templateUrl('inventories/groups/list/groups-list')).then((template) => {
                //     return html.concat(template);
                // });
                return html;
            },
                controller: 'NestedHostsListController'
        }
    },
    resolve: {
        Dataset: ['NestedHostsListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
            (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope) => {
                // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                let path, interpolator;
                if (GetBasePath(list.basePath)) {
                    path = GetBasePath(list.basePath);
                } else {
                    interpolator = $interpolate(list.basePath);
                    path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                }
                path = `api/v2/groups/${$stateParams.group_id}/all_hosts`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
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
