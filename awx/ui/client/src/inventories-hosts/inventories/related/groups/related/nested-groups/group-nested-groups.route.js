import {templateUrl} from '../../../../../../shared/template-url/template-url.factory';
import { N_ } from '../../../../../../i18n';

export default {
    name: 'inventories.edit.groups.edit.nested_groups',
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
    ncyBreadcrumb: {
        parent: "inventories.edit.groups.edit",
        label: N_("ASSOCIATED GROUPS")
    },
    views: {
        // 'related@inventories.edit.groups.edit': {
        'related': {
            templateProvider: function(NestedGroupListDefinition, generateList, $templateRequest) {
                let list = _.cloneDeep(NestedGroupListDefinition);

                let html = generateList.build({
                    list: list,
                    mode: 'edit'
                });

                return $templateRequest(templateUrl('inventories-hosts/inventories/related/groups/related/nested-groups/group-nested-groups-disassociate')).then((template) => {
                    return html.concat(template);
                });
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
                    path = GetBasePath('groups') + $stateParams.group_id + '/children';
                }
                else if($stateParams.host_id){
                    path = GetBasePath('hosts') + $stateParams.host_id + '/all_groups';
                }
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        host: ['$stateParams', 'HostsService', function($stateParams, HostsService) {
            if($stateParams.host_id){
                return HostsService.get({ id: $stateParams.host_id }).then(function(res) {
                    return res.data.results[0];
                });
            }
        }],
        inventoryData: ['InventoriesService', '$stateParams', 'host', function(InventoriesService, $stateParams, host) {
            var id = ($stateParams.inventory_id) ? $stateParams.inventory_id : host.summary_fields.inventory.id;
            return InventoriesService.getInventory(id).then(res => res.data);
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
