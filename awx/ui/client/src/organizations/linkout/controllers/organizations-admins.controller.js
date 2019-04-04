/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$stateParams', '$scope', 'Rest', '$state',
    '$compile', 'Wait', 'OrgAdminList', 'OrgAdminsDataset', 'i18n',
    'Prompt', 'ProcessErrors', 'GetBasePath', '$filter',
    function($stateParams, $scope, Rest, $state,
        $compile, Wait, OrgAdminList, OrgAdminsDataset, i18n,
        Prompt, ProcessErrors, GetBasePath, $filter) {

        var orgBase = GetBasePath('organizations');

        init();

        function init() {
            // search init
            $scope.list = OrgAdminList;
            $scope.user_dataset = OrgAdminsDataset.data;
            $scope.users = $scope.user_dataset.results;

            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .then(({data}) => {
                    $scope.organization_name = data.name;
                    $scope.name = data.name;
                    $scope.org_id = data.id;
                    $scope.canAddAdmins = data.summary_fields.user_capabilities.edit;

                    $scope.orgRelatedUrls = data.related;

                });
        }

        $scope.addUsers = function() {
            $compile("<add-users add-users-type='admins' class='AddUsers'></add-users>")($scope);
        };

        $scope.editUser = function(id) {
            $state.go('users.edit', { user_id: id });
        };

        $scope.deleteUser = function(id, name) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = orgBase + $stateParams.organization_id + '/admins/';
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
                body: `<div class="Prompt-bodyQuery">${i18n._('Are you sure you want to remove the following administrator from this organization?')}</div><div class="Prompt-bodyTarget">` + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };

    }
];
