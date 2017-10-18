export default {
    params: {
        inventory_script_search: {
            value: {
                page_size: "5",
                order_by: "name",
                role_level: "admin_role",
            },
            dynamic: true,
            squash: ""
        }
    },
    data: {
        basePath: "inventory_scripts",
        formChildState: true
    },
    ncyBreadcrumb: {
        skip: true
    },
    views: {
        'modal': {
            templateProvider: function(ListDefinition, generateList) {
                let list_html = generateList.build({
                    mode: 'lookup',
                    list: ListDefinition,
                    input_type: 'radio'
                });
                return `<lookup-modal>${list_html}</lookup-modal>`;

            }
        }
    },
    resolve: {
        ListDefinition: ['InventoryScriptsList', function(list) {
            return list;
        }],
        OrganizationId: ['ListDefinition', 'InventoriesService', '$stateParams', '$rootScope',
            function(list, InventoriesService, $stateParams, $rootScope){
                if($rootScope.$$childTail &&
                    $rootScope.$$childTail.$resolve &&
                    $rootScope.$$childTail.$resolve.hasOwnProperty('inventoryData')){
                        return $rootScope.$$childTail.$resolve.inventoryData.summary_fields.organization.id;
                }
                else {
                    return InventoriesService.getInventory($stateParams.inventory_id).then(res => res.data.summary_fields.organization.id);
                }
        }],
        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$interpolate', '$rootScope', '$state', 'OrganizationId',
            (list, qs, $stateParams, GetBasePath, $interpolate, $rootScope, $state, OrganizationId) => {

                $stateParams[`${list.iterator}_search`].role_level = "admin_role";
                $stateParams[`${list.iterator}_search`].organization = OrganizationId;

                return qs.search(GetBasePath('inventory_scripts'), $stateParams[`${list.iterator}_search`]);
            }
        ]
    },
    onExit: function($state) {
        if ($state.transition) {
            $('#form-modal').modal('hide');
            $('.modal-backdrop').remove();
            $('body').removeClass('modal-open');
        }
    }
};
