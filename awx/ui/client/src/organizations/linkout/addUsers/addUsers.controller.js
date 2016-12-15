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

export default ['$scope', '$rootScope', 'ProcessErrors', 'GetBasePath',
'SelectionInit', 'templateUrl', '$state', 'Rest', '$q', 'Wait', '$window',
function($scope, $rootScope, ProcessErrors, GetBasePath,
    SelectionInit, templateUrl, $state, Rest, $q, Wait, $window) {
    $scope.$on("linkLists", function() {

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
            $scope.$on('selectedOrDeselected', function(e, value) {
                let item = value.value;

                if (item.isSelected) {
                    $scope.selectedItems.push(item.id);
                }
                else {
                    $scope.selectedItems = _.remove($scope.selectedItems, { id: item.id });
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
