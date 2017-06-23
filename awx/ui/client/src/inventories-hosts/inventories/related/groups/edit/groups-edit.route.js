export default {
    name: "inventories.edit.groups.edit",
    url: "/edit/:group_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.groups",
        label: "{{breadcrumb.group_name}}"
    },
    views: {
        'groupForm@inventories': {
            templateProvider: function(GenerateForm, GroupForm) {
                let form = GroupForm;
                return GenerateForm.buildHTML(form, {
                    mode: 'edit',
                    related: false
                });
            },
            controller: 'GroupEditController'
        }
    },
    resolve: {
        groupData: ['$stateParams', 'GroupsService', function($stateParams, GroupsService) {
            return GroupsService.get({ id: $stateParams.group_id }).then(res => res.data.results[0]);
        }]
    }
};
