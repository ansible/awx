export default ['$compile', '$scope', '$stateParams', '$state', 'Rest', 'UserList', 'InventoryList', 'JobTemplateList', 'TeamList', 'ProjectList', 'generateList', 'SearchInit', 'PaginateInit', function($compile, $scope, $stateParams, $state, Rest, UserList, InventoryList, JobTemplateList, TeamList, ProjectList, GenerateList, SearchInit, PaginateInit) {

    var getList = function(mode) {
        var list = {};
        if (mode === 'users') {
            list = _.cloneDeep(UserList);
            list.emptyListText = "Please add items to this list";
            list.actions.add.label = "Add a user to the organization";
            list.actions.add.buttonContent = '&#43; ADD user';
            list.actions.add.awToolTip = 'Add existing user to organization';
            list.actions.add.ngClick = 'addUsers()';
        } else if (mode === 'inventories') {
            list = _.cloneDeep(InventoryList);
            list.emptyListText = "List is empty";
            delete list.actions.add;
        } else if (mode === 'job_templates') {
            list = _.cloneDeep(JobTemplateList);
            list.emptyListText = "List is empty";
            delete list.actions.add;
        } else if (mode === 'teams') {
            list = _.cloneDeep(TeamList);
            list.emptyListText = "List is empty";
            delete list.actions.add;
        } else if (mode === 'projects') {
            list = _.cloneDeep(ProjectList);
            list.emptyListText = "List is empty";
            delete list.actions.add;
        } else if (mode === 'admins') {
            list = _.cloneDeep(UserList);
            list.emptyListText = "Please add items to this list";
            list.actions.add.buttonContent = '&#43; ADD administrator';
            list.actions.add.awToolTip = 'Add existing user to organization as administrator';
            list.actions.add.ngClick = 'addUsers()';
        }
        return list;
    };

    var getUrl = function(mode, data) {
        var url = "";
        if (mode === 'users') {
            url = data.related.users;
        } else if (mode === 'inventories') {
            url = data.related.inventories;
        } else if (mode === 'job_templates') {
            url = "/api/v1/job_templates/?project__organization=" + data.id;
        } else if (mode === 'teams') {
            url = data.related.teams;
        } else if (mode === 'projects') {
            url = data.related.projects;
        } else if (mode === 'admins') {
            url = data.related.admins;
        }
        return url;
    };

    Rest.setUrl("/api/v1/organizations/" + $stateParams.organization_id);
    Rest.get()
        .success(function (data) {
            // include name of item in listTitle
            var mode = $state.current.name.split(".")[1],
                listTitle = data.name +
                    "<div class='List-titleLockup'></div>" +
                    mode.replace('_', ' '),
                list,
                url,
                generator = GenerateList;
            $scope.$parent.activeCard = parseInt($stateParams.organization_id);
            $scope.$parent.activeMode = mode;
            $scope.org_name = data.name;
            $scope.org_id = data.id;
            var listMode = (mode === 'admins') ? 'users' : mode;

            list = getList(mode);
            list.listTitle = listTitle;

            url = getUrl(mode, data);

            $scope.orgRelatedUrls = data.related;

            generator
                .inject(list, { mode: 'edit', scope: $scope });

            $scope.addUsers = function () {
                $compile("<add-users class='AddUsers'></add-users>")($scope);
            };

            SearchInit({
                scope: $scope,
                set: listMode,
                list: list,
                url: url
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url: url
            });
            $scope.search(list.iterator);
        });
}];
