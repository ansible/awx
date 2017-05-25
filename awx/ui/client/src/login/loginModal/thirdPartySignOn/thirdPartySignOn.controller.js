/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:thirdPartySignOn
 * @description
 * Controller for handling third party supported login options.
 */

export default ['$window', '$scope', 'thirdPartySignOnService',
    function ($window, $scope, thirdPartySignOnService) {

        thirdPartySignOnService(
            {scope: $scope, url: "api/v2/auth/"}).then(function (data) {
            if (data && data.options && data.options.length > 0) {
                $scope.thirdPartyLoginSupported = true;
                $scope.loginItems = data.options;
            } else {
                $scope.thirdPartyLoginSupported = false;
            }

            if (data && data.error) {
                $scope.$parent.thirdPartyAttemptFailed = data.error;
            }
        });

        $scope.goTo = function(link) {
            // this is used because $location only lets you navigate inside
            // the "/#/" path, and these are API urls.
            $window.location.href = link;
        };
    }];
