export default {
    params: {
        credential_search: {
            value: {
                page_size:"5",
                order_by:"name",
                role_level:"use_role",
                kind: null,
                credential_type__kind: null
            },
            dynamic:true,
            squash:""
        }
    },
    data: {
        basePath:"credentials",
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
        ListDefinition: ['CredentialList', function(list) {
            return list;
        }],
        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', '$transition$',
            (list, qs, $stateParams, GetBasePath, $transition$) => {
                const toState = $transition$.to();
                toState.params.credential_search.value.credential_type__namespace = _.get($stateParams, 'credential_search.credential_type__namespace', null);
                toState.params.credential_search.value.credential_type__kind = _.get($stateParams, 'credential_search.credential_type__kind', null);
                return qs.search(GetBasePath('credentials'), $stateParams[`${list.iterator}_search`]);
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
