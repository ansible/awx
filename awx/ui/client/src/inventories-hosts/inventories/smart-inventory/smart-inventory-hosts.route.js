import { N_ } from '../../../i18n';

export default {
    name: "inventories.editSmartInventory.hosts",
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
        label: N_("HOSTS")
    },
    views: {
        'related': {
            templateProvider: function(ListDefinition, generateList) {
                let list = _.cloneDeep(ListDefinition);
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
            list.basePath = GetBasePath('inventory') + $stateParams.smartinventory_id + '/hosts';
            delete list.actions.create;
            delete list.fields.groups;
            delete list.fieldActions.delete;
            delete list.fieldActions.edit;
            delete list.fieldActions.view.ngShow;
            let toggleHost = list.staticColumns.find((el) => { return el.field === 'toggleHost'; });
            toggleHost.content.ngDisabled = true;
            list.fields.name.columnClass = 'col-lg-8 col-md-11 col-sm-8 col-xs-7';
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
            return InventoriesService.rootHostsUrl($stateParams.smartinventory_id);
        }],
        hostsDataset: ['ListDefinition', 'QuerySet', '$stateParams', 'hostsUrl', (list, qs, $stateParams, hostsUrl) => {
            let path = hostsUrl;
            return qs.search(path, $stateParams[`${list.iterator}_search`]);
        }],
        inventoryData: ['InventoriesService', '$stateParams', function(InventoriesService, $stateParams) {
            return InventoriesService.getInventory($stateParams.smartinventory_id).then(res => res.data);
        }]
    }
};
