export default {
    name: "inventories.edit.inventory_sources.edit",
    url: "/edit/:inventory_source_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.inventory_sources",
        label: '{{breadcrumb.inventory_source_name}}'
    },
    views: {
        'groupForm@inventories': {
            templateProvider: function(GenerateForm, SourcesFormDefinition) {
                let form = SourcesFormDefinition;
                return GenerateForm.buildHTML(form, {
                    mode: 'edit',
                    related: false
                });
            },
            controller: 'SourcesEditController'
        }
    },
    resolve: {
        inventorySource: ['InventorySourceModel', '$stateParams', (InventorySource, $stateParams) => {
            return new InventorySource('get', $stateParams.inventory_source_id);
        }],
        inventorySourcesOptions: ['InventoriesService', '$stateParams', function(InventoriesService, $stateParams) {
            return InventoriesService.inventorySourcesOptions($stateParams.inventory_id)
                .then((response) => response.data);
        }]
    }
};
