/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['templateUrl', 'i18n', function(templateUrl, i18n) {
    return {
        restrict: 'E',
        scope: true,
        replace: true,
        templateUrl: templateUrl('activity-stream/streamDropdownNav/stream-dropdown-nav'),
        controller: ['$scope', '$state', '$stateParams','CreateSelect2', function($scope, $state, $stateParams, CreateSelect2) {

            $scope.streamTarget = ($state.params && $state.params.target) ? $state.params.target : 'dashboard';

            $scope.options = [
                {label: i18n._('All Activity'), value: 'dashboard'},
                {label: i18n._('Credentials'), value: 'credential'},
                {label: i18n._('Hosts'), value: 'host'},
                {label: i18n._('Inventories'), value: 'inventory'},
                {label: i18n._('Inventory Scripts'), value: 'inventory_script'},
                {label: i18n._('Jobs'), value: 'job'},
                {label: i18n._('Organizations'), value: 'organization'},
                {label: i18n._('Projects'), value: 'project'},
                {label: i18n._('Schedules'), value: 'schedule'},
                {label: i18n._('Teams'), value: 'team'},
                {label: i18n._('Templates'), value: 'template'},
                {label: i18n._('Users'), value: 'user'}
            ];

            CreateSelect2({
                element:'#stream-dropdown-nav',
                multiple: false
            });

            $scope.changeStreamTarget = function(){
                if($scope.streamTarget && $scope.streamTarget === 'dashboard') {
                    // Just navigate to the base activity stream
                    $state.go('activityStream', {target: null, activity_search: {page_size:"20", order_by: '-timestamp'}});
                }
                else {
                    let search =  _.merge($stateParams.activity_search, {
                        or__object1__in: $scope.streamTarget && $scope.streamTarget === 'template' ? 'job_template,workflow_job_template' : $scope.streamTarget,
                        or__object2__in: $scope.streamTarget && $scope.streamTarget === 'template' ? 'job_template,workflow_job_template' : $scope.streamTarget
                    });
                    // Attach the taget to the query parameters
                    $state.go('activityStream', {target: $scope.streamTarget, activity_search: search});
                }

            };
        }],
    };
}];
