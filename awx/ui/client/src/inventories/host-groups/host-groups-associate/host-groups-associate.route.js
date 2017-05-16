export default {
    name: 'hosts.edit.groups.associate',
    squashSearchUrl: true,
    url: '/associate?inventory_id',
    params: {
        associate_group_search: {
            value: {order_by: 'name', page_size: '5', role_level: 'admin_role'},
            dynamic: true
        }
    },
    ncyBreadcrumb:{
        skip:true
    },
    views: {
        [`modal@hosts.edit`]: {
            templateProvider: function(ListDefinition, generateList) {

                let list_html = generateList.build({
                    mode: 'lookup',
                    list: ListDefinition,
                    input_type: 'radio'
                });

                return `<host-groups-associate>${list_html}</host-groups-associate>`;
            }
        }
    },
    resolve: {
        ListDefinition: ['GroupList', (GroupList) => {
            return GroupList;
        }],
        groupsDataset: ['QuerySet', '$stateParams', 'GetBasePath',
            function(qs, $stateParams, GetBasePath) {
                let path = GetBasePath('groups');
                return qs.search(path, $stateParams.associate_group_search);
            }
        ]
    },
    onExit: function($state) {
        if ($state.transition) {
            $('#add-permissions-modal').modal('hide');
            $('.modal-backdrop').remove();
            $('body').removeClass('modal-open');
        }
    },
};
