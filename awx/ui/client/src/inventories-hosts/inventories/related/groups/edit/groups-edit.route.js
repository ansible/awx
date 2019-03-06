export default {
    name: "inventories.edit.groups.edit",
    url: "/edit/:group_id",
    ncyBreadcrumb: {
        parent: "inventories.edit.groups",
        label: "{{breadcrumb.group_name}}"
    },
    resolve: {
        groupData: ['$stateParams', 'GroupsService', function($stateParams, GroupsService) {
            return GroupsService.get({ id: $stateParams.group_id }).then(response => response.data.results[0]);
        }]
    }
};
