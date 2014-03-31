
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
GetBasePath, Wait, Breadcrumbs, Find, LoadDialogPartial, LoadSchedulesScope) {
    
    ClearScope();

    var base, e, id, url, parentObject,
        schedules_scope = $scope.$new();

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

        url += "schedules/";

        LoadSchedulesScope({
            parent_scope: $scope,
            scope: schedules_scope,
            list: SchedulesList,
            id: 'schedule-list-target',
            url: url
        });
    });

    // Load the parent object
    Wait('start');
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
}

ScheduleEditController.$inject = [ '$scope', '$compile', '$location', '$routeParams', 'SchedulesList', 'Rest', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope',
    'GetBasePath', 'Wait', 'Breadcrumbs', 'Find', 'LoadDialogPartial', 'LoadSchedulesScope' ];