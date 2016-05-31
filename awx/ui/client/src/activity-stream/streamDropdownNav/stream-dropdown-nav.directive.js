/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['templateUrl', function(templateUrl) {
    return {
        restrict: 'E',
        scope: true,
        replace: true,
        templateUrl: templateUrl('activity-stream/streamDropdownNav/stream-dropdown-nav'),
        controller: ['$scope', '$state', 'CreateSelect2', function($scope, $state, CreateSelect2) {

            $scope.streamTarget = ($state.params && $state.params.target) ? $state.params.target : 'dashboard';

            $scope.options = [
                {label: 'All Activity', value: 'dashboard'},
                {label: 'Credentials', value: 'credential'},
                {label: 'Hosts', value: 'host'},
                {label: 'Inventories', value: 'inventory'},
                {label: 'Inventory Scripts', value: 'inventory_script'},
                {label: 'Job Templates', value: 'job_template'},
                {label: 'Jobs', value: 'job'},
                {label: 'Organizations', value: 'organization'},
                {label: 'Projects', value: 'project'},
                {label: 'Schedules', value: 'schedule'},
                {label: 'Teams', value: 'team'},
                {label: 'Users', value: 'user'}
            ];

            CreateSelect2({
                element:'#stream-dropdown-nav',
                multiple: false
            });

            $scope.changeStreamTarget = function(){

                if($scope.streamTarget && $scope.streamTarget === 'dashboard') {
                    // Just navigate to the base activity stream
                    $state.go('activityStream', {}, {inherit: false});
                }
                else {
                    // Attach the taget to the query parameters
                    $state.go('activityStream', {target: $scope.streamTarget}, {inherit: false});
                }

            };
        }],
    };
}];
