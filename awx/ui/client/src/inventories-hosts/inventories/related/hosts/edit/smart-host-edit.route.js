export default {
    name: "inventories.editSmartInventory.hosts.edit",
    url: "/edit/:host_id",
    ncyBreadcrumb: {
        parent: "inventories.editSmartInventory.hosts",
        label: "{{breadcrumb.host_name}}"
    },
    views: {
        'hostForm@inventories': {
            templateProvider: function(GenerateForm, RelatedHostsFormDefinition) {
                let form = _.cloneDeep(RelatedHostsFormDefinition);
                form.stateTree = 'inventories.editSmartInventory.hosts';
                delete form.related;
                return GenerateForm.buildHTML(form, {
                    mode: 'edit',
                    related: false
                });
            },
            controller: 'RelatedHostEditController'
        }
    },
    resolve: {
        host: ['$stateParams', 'InventoriesService', function($stateParams, InventoriesService) {
            return InventoriesService.getHost($stateParams.smartinventory_id, $stateParams.host_id).then(function(res) {
                return res.data.results[0];
            });
        }]
    }
};
