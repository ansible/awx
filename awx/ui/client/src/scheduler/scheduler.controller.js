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
    '$scope', '$compile', '$location', '$stateParams', 'SchedulesList', 'Rest', 'ProcessErrors', 'ReturnToCaller', 'ClearScope',
        'GetBasePath', 'Wait', 'Find', 'LoadDialogPartial', 'LoadSchedulesScope', 'GetChoices', 'Stream',
    function ($scope, $compile, $location, $stateParams,
    SchedulesList, Rest, ProcessErrors, ReturnToCaller, ClearScope,
    GetBasePath, Wait, Find, LoadDialogPartial, LoadSchedulesScope, GetChoices,
    Stream) {

        ClearScope();

        var base, e, id, url, parentObject;

        base = $location.path().replace(/^\//, '').split('/')[0];

        if ($scope.removePostRefresh) {
            $scope.removePostRefresh();
        }
        $scope.removePostRefresh = $scope.$on('PostRefresh', function() {
            var list = $scope.schedules;
            list.forEach(function(element, idx) {
                list[idx].play_tip = (element.enabled) ? 'Schedule is Active. Click to temporarily stop.' : 'Schedule is temporarily stopped. Click to activate.';
            });
        });

        if ($scope.removeParentLoaded) {
            $scope.removeParentLoaded();
        }
        $scope.removeParentLoaded = $scope.$on('ParentLoaded', function() {
            url += "schedules/";
            SchedulesList.well = true;

            // include name of item in listTitle
            SchedulesList.listTitle = parentObject.name + "<div class='List-titleLockup'></div>Schedules";

            LoadSchedulesScope({
                parent_scope: $scope,
                scope: $scope,
                list: SchedulesList,
                id: 'schedule-list-target',
                url: url,
                pageSize: 20
            });
        });


        if ($scope.removeChoicesReady) {
            $scope.removeChocesReady();
        }
        $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
            // Load the parent object
            id = $stateParams.id;
            url = GetBasePath(base) + id + '/';
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
            url: GetBasePath('unified_jobs'),   //'/static/sample/data/types/data.json'
            field: 'type',
            variable: 'type_choices',
            callback: 'choicesReady'
        });
    }];
