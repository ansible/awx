/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Schedules
 * @description This controller's for schedules
*/

export default [
    '$scope', '$location', '$routeParams', 'SchedulesList', 'Rest',
    'ProcessErrors', 'GetBasePath', 'Wait','LoadSchedulesScope', 'GetChoices',
    'Stream', 'management_job', '$rootScope',
    function($scope, $location, $routeParams, SchedulesList, Rest,
        ProcessErrors, GetBasePath, Wait, LoadSchedulesScope, GetChoices,
        Stream, management_job, $rootScope) {
            var base, id, url, parentObject;
            $scope.management_job = management_job;
            base =  $location.path().replace(/^\//, '').split('/')[0];

            // GetBasePath('management_job') must map to 'system_job_templates'
            // to match the api syntax
            $rootScope.defaultUrls.management_jobs = 'api/v1/system_job_templates/';

            if ($scope.removePostRefresh) {
                $scope.removePostRefresh();
            }
            $scope.removePostRefresh = $scope.$on('PostRefresh', function() {
                var list = $scope.schedules;
                list.forEach(function(element, idx) {
                    list[idx].play_tip = (element.enabled) ? 'Schedule is Active.'+
                        ' Click to temporarily stop.' : 'Schedule is temporarily '+
                        'stopped. Click to activate.';
                });
            });

            if ($scope.removeParentLoaded) {
                $scope.removeParentLoaded();
            }
            $scope.removeParentLoaded = $scope.$on('ParentLoaded', function() {
                url += "schedules/";
                SchedulesList.well = true;
                LoadSchedulesScope({
                    parent_scope: $scope,
                    scope: $scope,
                    list: SchedulesList,
                    id: 'management_jobs_schedule',
                    url: url,
                    pageSize: 20
                });
            });

            if ($scope.removeChoicesReady) {
                $scope.removeChocesReady();
            }
            $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
                // Load the parent object
                id = $routeParams.management_job;
                url = GetBasePath('system_job_templates') + id + '/';
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        parentObject = data;
                        $scope.$emit('ParentLoaded');
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. GET returned: ' + status });
                    });
            });

            $scope.refreshJobs = function() {
                $scope.search(SchedulesList.iterator);
            };

            $scope.showActivity = function () {
                Stream({ scope: $scope });
            };

            Wait('start');

            GetChoices({
                scope: $scope,
                url: GetBasePath('system_jobs'),
                field: 'type',
                variable: 'type_choices',
                callback: 'choicesReady'
            });
        }
];
