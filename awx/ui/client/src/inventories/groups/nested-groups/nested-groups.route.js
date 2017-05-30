export default {
    url: "/nested_groups?{nested_group_search:queryset}",
    params: {
        nested_group_search: {
            value: {
                page_size: "20",
                order_by: "name"
            },
            dynamic: true,
            squash: ""
        }
    },
    views: {
        // 'related@inventories.edit.groups.edit': {
        'related': {
            templateProvider: function(NestedGroupListDefinition, generateList) {
                let list = _.cloneDeep(NestedGroupListDefinition);

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
                controller: 'NestedGroupsListController'
        }
    },
    resolve: {
        Dataset: ['NestedGroupListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
            (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope) => {
                // allow related list definitions to use interpolated $rootScope / $stateParams in basePath field
                let path, interpolator;
                if (GetBasePath(list.basePath)) {
                    path = GetBasePath(list.basePath);
                } else {
                    interpolator = $interpolate(list.basePath);
                    path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
                }
                if($stateParams.group_id){
                    path = `api/v2/groups/${$stateParams.group_id}/children`;
                }
                else if($stateParams.host_id){
                    path = GetBasePath('hosts') + $stateParams.host_id + '/all_groups';
                }
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService) {
            if($stateParams.host_id){
                return HostManageService.get({ id: $stateParams.host_id }).then(function(res) {
                    return res.data.results[0];
                });
            }
        }],
        inventoryData: ['InventoryManageService', '$stateParams', 'host', function(InventoryManageService, $stateParams, host) {
            var id = ($stateParams.inventory_id) ? $stateParams.inventory_id : host.summary_fields.inventory.id;
            return InventoryManageService.getInventory(id).then(res => res.data);
        }],
        canAdd: ['rbacUiControlService', '$state', 'GetBasePath', '$stateParams', function(rbacUiControlService, $state, GetBasePath, $stateParams) {
            return rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/groups")
                .then(function(res) {
                    return res.canAdd;
                })
                .catch(function() {
                    return false;
                });
        }]
    }
};
