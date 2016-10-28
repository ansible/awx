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

export default ['$scope', '$rootScope', 'ProcessErrors',  'generateList', 'GetBasePath',
'SelectionInit', 'templateUrl', '$state', 'Rest', '$q', 'Wait',
function($scope, $rootScope, ProcessErrors, generateList, GetBasePath,
    SelectionInit, templateUrl, $state, Rest, $q, Wait) {
    $scope.$on("linkLists", function() {
        var generator = generateList,
            //list = AddUserList,
            id = "addUsersList",
            mode = "add";

        if ($state.current.name.split(".")[1] === "users") {
            $scope.addType = "Users";
        } else {
            $scope.addType = "Administrators";
        }

        init();

        function init(){
            // search init
            $scope.list = $scope.$parent.add_user_list;
            $scope.add_user_dataset =  $scope.$parent.add_user_dataset;
            $scope.add_users = $scope.$parent.add_user_dataset.results;

            $scope.selectedItems = [];
            $scope.$on('selectedOrDeselected', (item)=>{
                throw {name: 'NotYetImplemented'};
            });
        }

        $scope.updateUsers = function() {

            var url, listToClose,

            payloads = $scope.selectedItems.map(function(val) {
                return {id: val.id};
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
    });
}];
