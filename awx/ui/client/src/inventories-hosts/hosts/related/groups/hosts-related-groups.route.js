import { N_ } from '../../../../i18n';
import {templateUrl} from '../../../../shared/template-url/template-url.factory';

export default {
    name: "hosts.edit.groups",
    url: "/groups?{group_search:queryset}",
    resolve: {
        Dataset: ['HostsRelatedGroupsList', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
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
            templateProvider: function(HostsRelatedGroupsList, generateList, $templateRequest) {
                let html = generateList.build({
                    list: HostsRelatedGroupsList,
                    mode: 'edit'
                });

                return $templateRequest(templateUrl('inventories-hosts/hosts/related/groups/hosts-related-groups')).then((template) => {
                    return html.concat(template);
                });
            },
            controller: 'HostsRelatedGroupsController'
        }
    }
};
