export default {
    name: 'users.edit.tokens.add.application',
    url: '/application?selected',
    searchPrefix: 'application',
    params: {
        application_search: {
            value: {
                page_size: 5,
                order_by: 'name'
            },
            dynamic: true,
            squash: ''
        }
    },
    data: {
        basePath: 'applications'
    },
    ncyBreadcrumb: {
        skip: true
    },
    views: {
        'application@users.edit.tokens.add': {
            templateProvider: (ListDefinition, generateList) => {
                const html = generateList.build({
                    mode: 'lookup',
                    list: ListDefinition,
                    input_type: 'radio'
                });

                return `<lookup-modal>${html}</lookup-modal>`;
            }
        }
    },
    resolve: {
        ListDefinition: [() => ({
            name: 'applications',
            iterator: 'application',
            hover: true,
            index: false,
            fields: {
                name: {
                    key: true,
                    label: 'Name',
                    columnClass: 'col-sm-6',
                    awToolTip: '{{application.description | sanitize}}',
                    dataPlacement: 'top'
                },
                organization: {
                    label: 'Organization',
                    columnClass: 'col-sm-6',
                    key: false,
                    ngBind: 'application.summary_fields.organization.name',
                    sourceModel: 'organization',
                    includeModal: true
                }
            }
        })],
        Dataset: ['QuerySet', 'GetBasePath', '$stateParams', 'ListDefinition',
            (qs, GetBasePath, $stateParams, list) => qs.search(
                GetBasePath('applications'),
                $stateParams[`${list.iterator}_search`]
            )
        ]
    },
    onExit ($state) {
        if ($state.transition) {
            $('#form-modal').modal('hide');
            $('.modal-backdrop').remove();
            $('body').removeClass('modal-open');
        }
    }
};
