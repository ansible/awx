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
    '$scope', '$compile', '$location', '$stateParams', 'SchedulesList', 'Rest',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'GetBasePath', 'Wait',
    'Find', 'LoadSchedulesScope', 'GetChoices', '$q', '$state',
    function ($scope, $compile, $location, $stateParams,
    SchedulesList, Rest, ProcessErrors, ReturnToCaller, ClearScope,
    GetBasePath, Wait, Find, LoadSchedulesScope, GetChoices,
    $q, $state) {
        var schedList = _.cloneDeep(SchedulesList);

        ClearScope();

        var base, id, url,parentObject, title;

        base = $location.path().replace(/^\//, '').split('/')[0];
        if (base === 'management_jobs') {
            $scope.base = base = 'system_job_templates';
        }
        if ($stateParams.job_type){
            $scope.job_type = $stateParams.job_type;
        }

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

            $scope.canAdd = false;

            Rest.setUrl(url);
            Rest.options()
                .success(function(data) {
                    if (data.actions.POST) {
                        $scope.canAdd = true;
                    }
                });

            schedList.well = true;

            // include name of item in listTitle
            let escaped_title =  $("<span>").text(title ? title : parentObject.name)[0].innerHTML;
            schedList.listTitle = `${escaped_title}<div class='List-titleLockup'></div>Schedules`;

            schedList.basePath = parentObject.url + "schedules";

            LoadSchedulesScope({
                parent_scope: $scope,
                scope: $scope,
                list: schedList,
                id: 'schedule-list-target',
                url: url,
                pageSize: 20,
            });
        });

        function getUrl(){
            if($stateParams.inventory_id){
                url = GetBasePath('groups') + $stateParams.id + '/';
                Rest.setUrl(url);
                var promise;
                promise = Rest.get();
                return promise.then(function (data) {
                        url = data.data.related.inventory_source;
                        title = data.data.name;
                    }).catch(function (response) {
                    ProcessErrors(null, response.data, response.status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to get inventory group info. GET returned status: ' +
                        response.status
                    });
                });
            }
            else{
                url =  GetBasePath(base) + id + '/';
                return $q.when(url);
            }
        }

        if ($scope.removeChoicesReady) {
            $scope.removeChocesReady();
        }
        $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
            // Load the parent object
            id = $stateParams.id;
            getUrl().then(function(){
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        parentObject = data;
                        $scope.name = data.name;
                        $scope.$emit('ParentLoaded');
                    })
                    .error(function(data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. GET returned: ' + status });
                    });
            });
        });

        $scope.refreshJobs = function() {
            $scope.search(SchedulesList.iterator);
        };

        $scope.formCancel = function() {
            $state.go('^', {}, {reload: true});
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
