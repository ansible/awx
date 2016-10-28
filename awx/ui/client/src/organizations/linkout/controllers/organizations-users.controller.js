/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$stateParams', '$scope', 'OrgUserList', 'AddUserList','Rest', '$state',
    'generateList', '$compile', 'Wait', 'OrgUsersDataset', 'AddUsersDataset',
    'Prompt', 'ProcessErrors', 'GetBasePath', '$filter',
    function($stateParams, $scope, OrgUserList, AddUserList, Rest, $state, GenerateList,
        $compile, Wait, OrgUsersDataset, AddUsersDataset, Prompt, ProcessErrors,
        GetBasePath, $filter) {

        var orgBase = GetBasePath('organizations');

        init();

        function init() {
            // search init
            $scope.list = OrgUserList;
            $scope.add_user_list = AddUserList;
            $scope.user_dataset = OrgUsersDataset.data;
            $scope.users = $scope.user_dataset.results;
            $scope.add_user_dataset = AddUsersDataset.data;
            $scope.add_users = $scope.add_user_dataset.results;


            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .success(function(data) {
                    $scope.organization_name = data.name;
                    $scope.org_id = data.id;

                    $scope.orgRelatedUrls = data.related;

                });
        }

        $scope.addUsers = function() {
            $compile("<add-users add-users-type='user' class='AddUsers'></add-users>")($scope);
        };

        $scope.editUser = function(id) {
            $state.go('users.edit', { user_id: id });
        };

        $scope.deleteUser = function(id, name) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = orgBase + $stateParams.organization_id + '/users/';
                Rest.setUrl(url);
                Rest.post({
                        id: id,
                        disassociate: true
                    }).success(function() {
                        $state.go('.', null, { reload: true });
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: 'Delete',
                body: '<div class="Prompt-bodyQuery">Are you sure you want to remove the following user from this organization?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: 'DELETE'
            });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };

    }
];
