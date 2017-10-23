export default {
    name: "inventories.edit.hosts.edit",
    url: "/edit/:host_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.hosts",
        label: "{{breadcrumb.host_name}}"
    },
    views: {
        'hostForm@inventories': {
            templateProvider: function(GenerateForm, RelatedHostsFormDefinition) {
                let form = RelatedHostsFormDefinition;
                return GenerateForm.buildHTML(form, {
                    mode: 'edit',
                    related: false
                });
            },
            controller: 'RelatedHostEditController'
        }
    },
    resolve: {
        host: ['$stateParams', 'HostsService', function($stateParams, HostsService) {
            return HostsService.get({ id: $stateParams.host_id }).then((response) => response.data.results[0]);
        }]
    }
};
