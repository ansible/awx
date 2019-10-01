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

            if($state.params && $state.params.target) {
                $scope.streamTarget = ($state.params.target === 'job_template' || $state.params.target === 'workflow_job_template') ? 'template' : $state.params.target;
            }
            else {
                $scope.streamTarget = 'dashboard';
            }

            $scope.options = [
                {label: i18n._('All Activity'), value: 'dashboard'},
                {label: i18n._('Applications'), value: 'o_auth2_application'},
                {label: i18n._('Tokens'), value: 'o_auth2_access_token'},
                {label: i18n._('Credentials'), value: 'credential'},
                {label: i18n._('Hosts'), value: 'host'},
                {label: i18n._('Inventories'), value: 'inventory'},
                {label: i18n._('Inventory Scripts'), value: 'custom_inventory_script'},
                {label: i18n._('Jobs'), value: 'job'},
                {label: i18n._('Notification Templates'), value: 'notification_template'},
                {label: i18n._('Organizations'), value: 'organization'},
                {label: i18n._('Projects'), value: 'project'},
                {label: i18n._('Credential Types'), value: 'credential_type'},
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
                    let search =  {
                        or__object1__in: $scope.streamTarget,
                        or__object2__in: $scope.streamTarget,
                        page_size: '20',
                        order_by: '-timestamp'
                    };

                    if ($scope.streamTarget && $scope.streamTarget === 'template') {
                        search.or__object1__in = 'job_template,workflow_job_template';
                        search.or__object2__in = 'job_template,workflow_job_template';
                    }

                    if ($scope.streamTarget && $scope.streamTarget === 'job') {
                        search.or__object1__in = 'job,workflow_approval';
                        search.or__object2__in = 'job,workflow_approval';
                    }

                    // Attach the taget to the query parameters
                    $state.go('activityStream', {target: $scope.streamTarget, id: null, activity_search: search});
                }

            };
        }],
    };
}];
