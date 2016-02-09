/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [function() {
    return {
        restrict: 'E',
        scope: true,
        replace: true,
        template: '<select class="form-control" ng-model="streamTarget" ng-options="opt.value as opt.label for opt in options" ng-change="changeStreamTarget()"></select>',
        controller: ['$scope', '$state', function($scope, $state) {

            $scope.streamTarget = ($state.params && $state.params.target) ? $state.params.target : 'dashboard';

            $scope.options = [
                {label: 'Credentials', value: 'credential'},
                {label: 'Dashboard', value: 'dashboard'},
                {label: 'Hosts', value: 'host'},
                {label: 'Inventories', value: 'inventory'},
                {label: 'Inventory Scripts', value: 'inventory_script'},
                {label: 'Job Templates', value: 'job_template'},
                {label: 'Management Jobs', value: 'management_job'},
                {label: 'Organizations', value: 'organization'},
                {label: 'Projects', value: 'project'},
                {label: 'Schedules', value: 'schedule'},
                {label: 'Teams', value: 'team'},
                {label: 'Users', value: 'user'}
            ];

            $scope.changeStreamTarget = function(){

                if($scope.streamTarget && $scope.streamTarget == 'dashboard') {
                    // Just navigate to the base activity stream
                    $state.go('activityStream', {}, {inherit: false, reload: true});
                }
                else {
                    // Attach the taget to the query parameters
                    $state.go('activityStream', {target: $scope.streamTarget});
                }

            }
        }],
    };
}];
