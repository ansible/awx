import { N_ } from '../../../i18n';

export default {
    name: "inventories.edit.inventory_sources",
    url: "/inventory_sources?{inventory_source_search:queryset}",
    params: {
        inventory_source_search: {
            value: {
                page_size: "20",
                order_by: "name"
            },
            dynamic: true,
            squash: ""
        }
    },
    data: {
        socket: {
            groups: {
                jobs: ["status_changed"]
            }
        }
    },
    ncyBreadcrumb: {
        parent: "inventories.edit",
        label: N_("SOURCES")
    },
    views: {
        'related': {
            templateProvider: function(SourcesListDefinition, generateList) {
                let list = _.cloneDeep(SourcesListDefinition);
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
            controller: 'SourcesListController'
        }
    },
    resolve: {
        inventorySourceOptions: ['SourcesService', (SourcesService) => {
            return SourcesService.options().then(res => res.data.actions.GET);
        }],
        Dataset: ['SourcesListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope',
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
        inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
        }],
        canAdd: ['rbacUiControlService', 'GetBasePath', '$stateParams', function(rbacUiControlService, GetBasePath, $stateParams) {
            return rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/inventory_sources")
                .then(function(res) {
                    return res.canAdd;
                })
                .catch(function() {
                    return false;
                });
        }]
    }
};
