/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  JobHosts.js
 *
 *  Controller functions for the Job Hosts Summary model.
 *
 */

'use strict';

function JobHostSummaryList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobHostList, GenerateList,
    LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, Refresh,
    JobStatusToolTip, Wait) {
    
    ClearScope();
    
    var list = JobHostList,
        defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_host_summaries/',
        view = GenerateList;
        
    // When viewing all summaries for a particular host, show job ID, otherwise row ID.
    //if (base === 'hosts') {
    //    list.index = false;
    //} else {
    //    list.index = true;
    //}

    $scope.selected = [];

    // control enable/disable/show of job specific view elements
    //if (base === 'hosts') {
        //$scope.job_id = null;
        //$scope.host_id = $routeParams.id;
    //} else {  
    //}

    $scope.job_id = $routeParams.id;
    $scope.host_id = null;

    if ($scope.RemoveSetHostLink) {
        $scope.RemoveSetHostLink();
    }
    $scope.RemoveSetHostLink = $scope.$on('setHostLink', function (e, inventory_id) {
        for (var i = 0; i < $scope.jobhosts.length; i++) {
            $scope.jobhosts[i].hostLinkTo = '/#/inventories/' + inventory_id + '/?host_name=' +
                encodeURI($scope.jobhosts[i].summary_fields.host.name);
        }
    });

    // After a refresh, populate any needed summary field values on each row
    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {

        view.inject(list, { mode: 'edit', scope: $scope });

        // Set status, tooltips, badges icons, etc.
        $scope.jobhosts.forEach(function(element, i) {
            $scope.jobhosts[i].host_name = ($scope.jobhosts[i].summary_fields.host) ? $scope.jobhosts[i].summary_fields.host.name : '';
            $scope.jobhosts[i].status = ($scope.jobhosts[i].failed) ? 'failed' : 'success';
            $scope.jobhosts[i].statusBadgeToolTip = JobStatusToolTip($scope.jobhosts[i].status) +
                " Click to view details.";
            if ($scope.jobhosts[i].summary_fields.host) {
                $scope.jobhosts[i].statusLinkTo = '/#/job_events/' + $scope.jobhosts[i].job + '/?host=' +
                    encodeURI($scope.jobhosts[i].summary_fields.host.name);
            }
            else {
                $scope.jobhosts[i].statusLinkTo = '/#/job_events/' + $scope.jobhosts[i].job;
            }
        });

        //if ($scope.job_id !== null && $scope.job_id !== undefined && $scope.job_id !== '') {
            // need job_status so we can show/hide refresh button
        Rest.setUrl(GetBasePath('jobs') + $scope.job_id + '/');
        Rest.get()
            .success(function (data) {
                LoadBreadCrumbs({
                    path: '/job_host_summaries/' + $scope.job_id,
                    title: $scope.job_id + ' - ' + data.summary_fields.job_template.name,
                    altPath: '/jobs'
                });
                $rootScope.breadcrumbs = [{
                    path: '/jobs',
                    title: $scope.job_id + ' - ' + data.summary_fields.job_template.name,
                }];
                $scope.job_status = data.status;
                if (!(data.status === 'pending' || data.status === 'waiting' || data.status === 'running')) {
                    if ($rootScope.timer) {
                        clearInterval($rootScope.timer);
                    }
                }
                $scope.$emit('setHostLink', data.inventory);
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to get job status for job: ' + $scope.job_id + '. GET status: ' + status
                });
            });
        //} else {
            // Make the host name appear in breadcrumbs
        //    LoadBreadCrumbs({
        //        path: '/hosts/' + $scope.host_id,
        //        title: (($scope.jobhosts.length > 0) ? $scope.jobhosts[0].summary_fields.host.name : 'Host')
        //    });
        //    if ($routeParams.inventory) {
        //        $scope.$emit('setHostLink', $routeParams.inventory);
        //    }
        //}
    });

    SearchInit({
        scope: $scope,
        set: 'jobhosts',
        list: list,
        url: defaultUrl
    });

    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });

    // Called from Inventories tab, host failed events link:
    if ($routeParams.host_name) {
        $scope[list.iterator + 'SearchField'] = 'host';
        $scope[list.iterator + 'SearchValue'] = $routeParams.host_name;
        $scope[list.iterator + 'SearchFieldLabel'] = list.fields.host.label;
    }

    $scope.search(list.iterator);


    $scope.showEvents = function (host_name, last_job) {
        // When click on !Failed Events link, redirect to latest job/job_events for the host
        Rest.setUrl(last_job);
        Rest.get()
            .success(function (data) {
                LoadBreadCrumbs({
                    path: '/jobs/' + data.id,
                    title: data.name
                });
                $location.url('/jobs/' + data.id + '/job_events/?host=' + encodeURI(host_name));
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to lookup last job: ' + last_job +
                    '. GET status: ' + status });
            });
    };

    $scope.showJob = function (id) {
        $location.path('/jobs/' + id);
    };

    $scope.refresh = function () {
        if ($scope.host_id === null) {
            $scope.jobSearchSpin = true;
            $scope.jobLoading = true;
            Wait('start');
            Refresh({
                scope: $scope,
                set: 'jobhosts',
                iterator: 'jobhost',
                url: $scope.current_url
            });
        }
    };

}

JobHostSummaryList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobHostList',
    'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'Refresh', 'JobStatusToolTip', 'Wait'
];