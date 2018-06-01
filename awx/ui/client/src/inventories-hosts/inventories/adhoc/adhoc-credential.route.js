export default {
    searchPrefix: 'credential',
    url: '/credential',
    data: {
        formChildState: true
    },
    params: {
        credential_search: {
            value: {
                page_size: '5',
                credential_type: null
            },
            squash: true,
            dynamic: true
        }
    },
    ncyBreadcrumb: {
        skip: true
    },
    views: {
        'related': {
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
        ListDefinition: ['CredentialList', function(CredentialList) {
            let list = _.cloneDeep(CredentialList);
            return list;
        }],
        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
            (list, qs, $stateParams, GetBasePath) => {
                let path = GetBasePath(list.name) || GetBasePath(list.basePath);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
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
