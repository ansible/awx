export default {
    params: {
        project_search: {
            value: {
                page_size:"5",
                order_by:"name",
                not__status:"never updated",
                role_level:"use_role",
            },
            dynamic:true,
            squash:""
        }
    },
    data: {
        basePath:"projects",
        formChildState:true
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
        ListDefinition: ['ProjectList', function(list) {
            return list;
        }],
        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
            (list, qs, $stateParams, GetBasePath) => {
                return qs.search(GetBasePath('projects'), $stateParams[`${list.iterator}_search`]);
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
