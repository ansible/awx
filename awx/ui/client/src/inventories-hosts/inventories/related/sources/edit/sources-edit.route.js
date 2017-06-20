import { N_ } from '../../../../../i18n';

export default {
    name: "inventories.edit.inventory_sources.edit",
    url: "/edit/:inventory_source_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.inventory_sources",
        label: N_("INVENTORY SOURCES")
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
        inventorySourceData: ['$stateParams', 'SourcesService', function($stateParams, SourcesService) {
            return SourcesService.get({id: $stateParams.inventory_source_id }).then(res => res.data.results[0]);
        }],
        inventorySourcesOptions: ['InventoriesService', '$stateParams', function(InventoriesService, $stateParams) {
            return InventoriesService.inventorySourcesOptions($stateParams.inventory_id)
                .then(function(res) {
                    return res.data;
                });
        }]
    }
};
