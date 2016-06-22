/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$stateParams', '$scope', 'UserList', 'Rest', '$state', 'generateList', '$compile',
        'SearchInit', 'PaginateInit', 'Wait', 'Prompt', 'ProcessErrors', 'GetBasePath',
        function($stateParams, $scope, UserList, Rest, $state, GenerateList, $compile,
        SearchInit, PaginateInit, Wait, Prompt, ProcessErrors, GetBasePath) {

            var list,
                url,
                generator = GenerateList,
                orgBase = GetBasePath('organizations');

            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .success(function (data) {
                    // include name of item in listTitle
                    var listTitle = data.name + "<div class='List-titleLockup'></div>ADMINS";

                    $scope.$parent.activeCard = parseInt($stateParams.organization_id);
                    $scope.$parent.activeMode = 'admins';
                    $scope.organization_name = data.name;
                    $scope.org_id = data.id;
                    var listMode = 'users';

                    list = _.cloneDeep(UserList);
                    delete list.actions.add;
                    list.searchRowActions = {
                        add: {
                            buttonContent: '&#43; ADD administrator',
                            awToolTip: 'Add existing user to organization as administrator',
                            actionClass: 'btn List-buttonSubmit',
                            ngClick: 'addUsers()'
                        }
                    };
                    url = data.related.admins;
                    list.listTitle = listTitle;
                    list.basePath = url;
                    list.searchSize = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
                    
                    $scope.orgRelatedUrls = data.related;

                    generator.inject(list, { mode: 'edit', scope: $scope, cancelButton: true });

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

            $scope.addUsers = function () {
                $compile("<add-users class='AddUsers'></add-users>")($scope);
            };

            $scope.editUser = function (id) {
                $state.transitionTo('users.edit', {user_id: id});
            };

            $scope.deleteUser = function (id, name) {
                var action = function () {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    var url = orgBase + $stateParams.organization_id + '/admins/';
                    Rest.setUrl(url);
                    Rest.post({
                        id: id,
                        disassociate: true
                    }).success(function () {
                        $scope.search(list.iterator);
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                    });
                };

                Prompt({
                    hdr: 'Delete',
                    body: '<div class="Prompt-bodyQuery">Are you sure you want to remove the following administrator from this organization?</div><div class="Prompt-bodyTarget">' + name + '</div>',
                    action: action,
                    actionText: 'DELETE'
                });
            };

            $scope.formCancel = function(){
                $scope.$emit("ReloadOrgListView");
                $state.go('organizations');
            };

        }
];
