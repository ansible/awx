/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$stateParams', '$scope', 'OrgUserList','Rest', '$state',
    '$compile', 'Wait', 'OrgUsersDataset',
    'Prompt', 'ProcessErrors', 'GetBasePath', '$filter', 'i18n',
    function($stateParams, $scope, OrgUserList, Rest, $state,
        $compile, Wait, OrgUsersDataset, Prompt, ProcessErrors,
        GetBasePath, $filter, i18n) {

        var orgBase = GetBasePath('organizations');

        init();

        function init() {
            // search init
            $scope.list = OrgUserList;
            $scope.user_dataset = OrgUsersDataset.data;
            $scope.users = $scope.user_dataset.results;

            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .then(({data}) => {
                    $scope.organization_name = data.name;
                    $scope.name = data.name;
                    $scope.org_id = data.id;

                    $scope.orgRelatedUrls = data.related;

                });
        }

        $scope.addUsers = function() {
            $compile("<add-users add-users-type='users' class='AddUsers'></add-users>")($scope);
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
                    }).then(() => {
                        $state.go('.', null, { reload: true });
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                body: `<div class="Prompt-bodyQuery">${i18n._('Are you sure you want to remove the following user from this organization?')}</div><div class="Prompt-bodyTarget">` + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };

    }
];
