
/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Schedules.js
 *
 *  Controller functions for the Schedule model.
 *
 */

'use strict';

function ScheduleEditController($scope, $compile, $location, $routeParams, SchedulesList, Rest, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
GetBasePath, Wait, Breadcrumbs, Find, LoadDialogPartial, LoadSchedulesScope, GetChoices, Stream) {
    
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
        // Add breadcrumbs
        LoadBreadCrumbs({
            path: $location.path().replace(/\/schedules$/,''),
            title: parentObject.name
        });
        e = angular.element(document.getElementById('breadcrumbs'));
        e.html(Breadcrumbs({ list: SchedulesList, mode: 'edit' }));
        $compile(e)($scope);

        url += "schedules/";
        SchedulesList.well = true;
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
        id = $routeParams.id;
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
}

ScheduleEditController.$inject = [ '$scope', '$compile', '$location', '$routeParams', 'SchedulesList', 'Rest', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope',
    'GetBasePath', 'Wait', 'Breadcrumbs', 'Find', 'LoadDialogPartial', 'LoadSchedulesScope', 'GetChoices', 'Stream' ];