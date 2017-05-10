export default {
    name: "inventories.edit.hosts.edit",
    url: "/edit/:host_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.hosts",
        label: "HOSTS"
    },
    views: {
        'hostForm@inventories': {
            templateProvider: function(GenerateForm, RelatedHostsFormDefinition, NestedHostsFormDefinition, $stateParams) {
                let form = RelatedHostsFormDefinition;
                if($stateParams.group_id){
                    form = NestedHostsFormDefinition;
                }
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
