/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Access
 * @description
 * Controller for handling permissions adding
 */

export default ['$scope', '$rootScope', 'ProcessErrors', 'GetBasePath', 'generateList',
'$state', 'Rest', '$q', 'Wait', '$window', 'QuerySet', 'UserList', 'i18n',
function($scope, $rootScope, ProcessErrors, GetBasePath, generateList,
    $state, Rest, $q, Wait, $window, qs, UserList, i18n) {
    $scope.$on("linkLists", function() {

        if ($state.current.name.split(".")[1] === "users") {
            $scope.addType = "Users";
        } else {
            $scope.addType = "Administrators";
        }

        let notAdminAlreadyParams = {};

        if ($scope.addType === 'Administrators') {
            Rest.setUrl(GetBasePath('organizations') + `${$state.params.organization_id}`);
            Rest.get().then(({data}) => {
                notAdminAlreadyParams.not__roles = data.summary_fields.object_roles.admin_role.id;
                init();
            });
        } else {
            init();
        }

        function init(){
            $scope.add_user_default_params = Object.assign({
                order_by: 'username',
                page_size: 5
            }, notAdminAlreadyParams);

            $scope.add_user_queryset = Object.assign({
                order_by: 'username',
                page_size: 5
            }, notAdminAlreadyParams);

            let list = _.cloneDeep(UserList);
            list.basePath = 'users';
            list.iterator = 'add_user';
            list.name = 'add_users';
            list.multiSelect = true;
            list.fields.username.ngClick = 'linkoutUser(add_user.id)';
            list.fields.username.columnClass = 'col-sm-4';
            list.fields.first_name.columnClass = 'col-sm-4';
            list.fields.last_name.columnClass = 'col-sm-4';
            list.layoutClass = 'List-staticColumnLayout--statusOrCheckbox';
            if ($scope.addType === 'Administrators') {
                list.emptyListText = i18n._('No users available to add as adminstrators');
            }
            delete list.actions;
            delete list.fieldActions;

            // Fire off the initial search
            qs.search(GetBasePath('users'), $scope.add_user_default_params)
                .then(function(res) {
                    $scope.add_user_dataset = res.data;
                    $scope.add_users = $scope.add_user_dataset.results;

                    let html = generateList.build({
                        list: list,
                        mode: 'edit',
                        title: false,
                        hideViewPerPage: true
                    });

                    $scope.list = list;

                    $scope.compileList(html);

                    $scope.$watchCollection('add_users', function () {
                        if($scope.selectedItems) {
                            // Loop across the users and see if any of them should be "checked"
                            $scope.add_users.forEach(function(row, i) {
                                if (_.includes($scope.selectedItems, row.id)) {
                                    $scope.add_users[i].isSelected = true;
                                }
                            });
                        }
                    });

                });

            $scope.selectedItems = [];
            $scope.$on('selectedOrDeselected', function(e, value) {
                let item = value.value;

                if (value.isSelected) {
                    $scope.selectedItems.push(item.id);
                }
                else {
                    // _.remove() Returns the new array of removed elements.
                    // This will pull all the values out of the array that don't
                    // match the deselected item effectively removing it
                    $scope.selectedItems = _.remove($scope.selectedItems, function(selectedItem) {
                        return selectedItem !== item.id;
                    });
                }
            });
        }

        $scope.updateUsers = function() {

            var url, listToClose,

            payloads = $scope.selectedItems.map(function(val) {
                return {id: val};
            });

            url = $scope.$parent.orgRelatedUrls[$scope.addUsersType];

            Wait('start');

            var requests = payloads
                .map(function(post) {
                    Rest.setUrl(url);
                    return Rest.post(post);
                });

            $q.all(requests)
                .then(function () {
                    $scope.closeModal();
                    $state.reload();
                }, function (error) {
                    Wait('stop');
                    $rootScope.$broadcast("refreshList", listToClose);
                    ProcessErrors(null, error.data, error.status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to post ' + $scope.addType +
                        ': POST returned status' + error.status
                    });
                });
        };

        $scope.linkoutUser = function(userId) {
            // Open the edit user form in a new tab so as not to navigate the user
            // away from the modal
            $window.open('/#/users/' + userId,'_blank');
        };
    });
}];
