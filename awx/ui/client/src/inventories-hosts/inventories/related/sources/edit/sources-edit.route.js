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
        }],
        isNotificationAdmin: ['Rest', 'ProcessErrors', 'GetBasePath', 'i18n',
            function(Rest, ProcessErrors, GetBasePath, i18n) {
                Rest.setUrl(`${GetBasePath('organizations')}?role_level=notification_admin_role&page_size=1`);
                return Rest.get()
                    .then(({data}) => {
                        return data.count > 0;
                    })
                    .catch(({data, status}) => {
                        ProcessErrors(null, data, status, null, {
                            hdr: i18n._('Error!'),
                            msg: i18n._('Failed to get organizations for which this user is a notification administrator. GET returned ') + status
                        });
                });
        }],
        ConfigData: ['ConfigService', 'ProcessErrors', 'i18n', (ConfigService, ProcessErrors, i18n) => {
            return ConfigService.getConfig()
                .then(response => response)
                .catch(({data, status}) => {
                    ProcessErrors(null, data, status, null, {
                        hdr: i18n._('Error!'),
                        msg: i18n._('Failed to get config. GET returned status: ') + status
                    });
                });
        }]
    }
};
