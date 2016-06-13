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

export default ['$scope', '$rootScope', 'ProcessErrors', 'UserList', 'generateList', 'GetBasePath', 'SelectionInit', 'SearchInit', 'templateUrl', 'PaginateInit', '$state', 'Rest', '$q', 'Wait', function($scope, $rootScope, ProcessErrors, UserList, generateList, GetBasePath, SelectionInit, SearchInit, templateUrl, PaginateInit, $state, Rest, $q, Wait) {
    $scope.$on("linkLists", function() {
        var generator = generateList,
            list = _.cloneDeep(UserList),
            url = GetBasePath("users"),
            set = "users",
            id = "addUsersList",
            mode = "add";

        if ($state.current.name.split(".")[1] === "users") {
            $scope.addType = "Users";
        } else {
            $scope.addType = "Administrators";
        }



        list.multiSelect = true;

        generator.inject(list, { id: id,
            title: false, mode: mode, scope: $scope });

        SearchInit({ scope: $scope, set: set,
            list: list, url: url });

        PaginateInit({ scope: $scope,
            list: list, url: url, pageSize: 5 });

        $scope.search(list.iterator);

        $scope.updateUsers = function() {
            var url, listToClose,
            payloads = $scope.selectedItems.map(function(val) {
                return {id: val.id};
            });
            if ($scope.addType === 'Users') {
                url = $scope.$parent.orgRelatedUrls.users;
                listToClose = 'user';
            } else {
                url = $scope.$parent.orgRelatedUrls.admins;
                listToClose = 'admin';
            }

            Wait('start');

            var requests = payloads
                .map(function(post) {
                    Rest.setUrl(url);
                    return Rest.post(post);
                });

            $q.all(requests)
                .then(function () {
                    Wait('stop');
                    $scope.$parent.search('user');
                    $scope.closeModal();
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
    });
}];
