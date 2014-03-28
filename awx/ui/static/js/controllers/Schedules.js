
/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Schedules.js
 *
 *  Controller functions for the Schedule model.
 *
 */

'use strict';

function ScheduleEditController($scope, $compile, $location, $routeParams, SchedulesList, GenerateList, Rest, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
GetBasePath, LookUpInit, Wait, SchedulerInit, Breadcrumbs, SearchInit, PaginateInit, PageRangeSetup, EditSchedule, AddSchedule, Find, ToggleSchedule, DeleteSchedule,
LoadDialogPartial) {
    
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
    $scope.removeScheduledLoaded = $scope.$on('ParentLoaded', function() {
        // Add breadcrumbs
        LoadBreadCrumbs({
            path: $location.path().replace(/\/schedules$/,''),
            title: parentObject.name
        });
        e = angular.element(document.getElementById('breadcrumbs'));
        e.html(Breadcrumbs({ list: SchedulesList, mode: 'edit' }));
        $compile(e)($scope);

        // Add schedules list
        GenerateList.inject(SchedulesList, {
            mode: 'edit',
            id: 'schedule-list-target',
            breadCrumbs: false,
            searchSize: 'col-lg-4 col-md-4 col-sm-3'
        });

        // Change later to use GetBasePath(base)
        //switch(base) {
        //    case 'job_templates':
        //        url = '/static/sample/data/schedules/data.json';
        //        break;
        //    case 'projects':
        //        url = '/static/sample/data/schedules/projects/data.json';
        //        break;
        //}
        
        url += "schedules/";

        SearchInit({
            scope: $scope,
            set: 'schedules',
            list: SchedulesList,
            url: url
        });

        PaginateInit({
            scope: $scope,
            list: SchedulesList,
            url: url
        });
        
        $scope.search(SchedulesList.iterator);
    });

    $scope.editSchedule = function(id) {
        var schedule = Find({ list: $scope.schedules, key: 'id', val: id });
        EditSchedule({ scope: $scope, schedule: schedule, url: url });
    };

    $scope.addSchedule = function() {
        var schedule = { };
        schedule.enabled =  true;
        AddSchedule({ scope: $scope, schedule: schedule, url: url });
    };

    if ($scope.removeScheduleRefresh) {
        $scope.removeScheduleRefresh();
    }
    $scope.removeScheduleToggled = $scope.$on('ScheduleRefresh', function() {
        $scope.search(SchedulesList.iterator);
    });

    $scope.toggleSchedule = function(id) {
        ToggleSchedule({
            scope: $scope,
            id: id,
            callback: 'ScheduleToggled'
        });
    };

    $scope.toggleSchedule = function(id) {
        ToggleSchedule({
            scope: $scope,
            id: id,
            callback: 'SchedulesRefresh'
        });
    };

    $scope.deleteSchedule = function(id) {
        DeleteSchedule({
            scope: $scope,
            id: id,
            callback: 'SchedulesRefresh'
        });
    };

    if ($scope.removeLoadParent) {
        $scope.removeLoadParent();
    }
    $scope.removeLoadParent = $scope.$on('LoadParent', function() {
        // Load the parent object
        id = $routeParams.id;
        url = GetBasePath(base) + id + '/';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                parentObject = data;
                $scope.$emit('ParentLoaded');
            })
            .error(function(status) {
                ProcessErrors($scope, null, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + ' failed. GET returned: ' + status });
            });
    });

    LoadDialogPartial({
        scope: $scope,
        element_id: 'schedule-dialog-target',
        callback: 'LoadParent',
    });
}

ScheduleEditController.$inject = ['$scope', '$compile', '$location', '$routeParams', 'SchedulesList', 'GenerateList', 'Rest', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller',
'ClearScope', 'GetBasePath', 'LookUpInit', 'Wait', 'SchedulerInit', 'Breadcrumbs', 'SearchInit', 'PaginateInit', 'PageRangeSetup', 'EditSchedule', 'AddSchedule',
'Find', 'ToggleSchedule', 'DeleteSchedule', 'LoadDialogPartial'
];