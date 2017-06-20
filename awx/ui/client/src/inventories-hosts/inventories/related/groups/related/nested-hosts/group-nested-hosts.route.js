import { N_ } from '../../../../../../i18n';
import {templateUrl} from '../../../../../../shared/template-url/template-url.factory';

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
            templateProvider: function(NestedHostsListDefinition, generateList, $templateRequest) {
                let list = _.cloneDeep(NestedHostsListDefinition);

                let html = generateList.build({
                    list: list,
                    mode: 'edit'
                });
                return $templateRequest(templateUrl('inventories-hosts/inventories/related/groups/related/nested-hosts/group-nested-hosts-disassociate')).then((template) => {
                    return html.concat(template);
                });
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
