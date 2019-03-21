import { N_ } from '../../../../../i18n';
import {templateUrl} from '../../../../../shared/template-url/template-url.factory';

export default {
    name: "inventories.edit.groups",
    url: "/groups?{group_search:queryset}",
    resolve: {
        listDefinition: ['GroupList', (list) => list],
        Dataset: ['listDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
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
        inventoryData: ['InventoriesService', '$stateParams', function(InventoriesService, $stateParams) {
            return InventoriesService.getInventory($stateParams.inventory_id).then(res => res.data);
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
        parent: "inventories.edit",
        label: N_("ALL GROUPS")
    },
    views: {
        'related': {
            templateProvider: function(listDefinition, generateList, $templateRequest, $stateParams, GetBasePath) {
                let list = _.cloneDeep(listDefinition);
                if($stateParams && $stateParams.group) {
                    list.basePath = GetBasePath('groups') + _.last($stateParams.group) + '/children';
                }
                else {
                    //reaches here if the user is on the root level group
                    list.basePath = GetBasePath('inventory') + $stateParams.inventory_id + '/groups';
                }

                let html = generateList.build({
                    list: list,
                    mode: 'edit'
                });
                // Include the custom group delete modal template
                return $templateRequest(templateUrl('inventories-hosts/inventories/related/groups/list/groups-list')).then((template) => {
                    return html.concat(template);
                });
            },
            controller: 'GroupsListController'
        }
    }
};
