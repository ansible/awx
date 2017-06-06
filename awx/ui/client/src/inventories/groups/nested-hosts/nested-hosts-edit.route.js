export default {
    name: "inventories.edit.groups.edit.nested_hosts.edit",
    url: "/edit/:host_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.groups.edit.nested_hosts",
        label: "{{breadcrumb.host_name}}"
    },
    views: {
        'hostForm@inventories': {
            templateProvider: function(GenerateForm, RelatedHostsFormDefinition, NestedHostsFormDefinition, $stateParams) {
                let form = ($stateParams.group_id) ? NestedHostsFormDefinition : RelatedHostsFormDefinition;
                return GenerateForm.buildHTML(form, {
                    mode: 'edit',
                    related: false
                });
            },
            controller: 'RelatedHostEditController'
        }
    },
    resolve: {
        host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService) {
            return HostManageService.get({ id: $stateParams.host_id }).then(function(res) {
                return res.data.results[0];
            });
        }]
    }
};
