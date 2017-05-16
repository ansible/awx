import { N_ } from '../../i18n';
import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: "hosts.edit.groups",
    url: "/groups?{group_search:queryset}",
    resolve: {
        Dataset: ['HostGroupsList', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
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
        }]
    },
    params: {
        group_search: {
            value: {
                page_size: "20",
                order_by: "name"
            },
            dynamic: true,
            squash: ""
        }
    },
    ncyBreadcrumb: {
        parent: "hosts.edit",
        label: N_("GROUPS")
    },
    views: {
        'related': {
            templateProvider: function(HostGroupsList, generateList, $templateRequest) {
                let html = generateList.build({
                    list: HostGroupsList,
                    mode: 'edit'
                });

                return $templateRequest(templateUrl('inventories/host-groups/host-groups')).then((template) => {
                    return html.concat(template);
                });
            },
            controller: 'HostGroupsController'
        }
    }
};
