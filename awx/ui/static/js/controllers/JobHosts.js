/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  JobHosts.js
 *
 *  Controller functions for the Job Hosts Summary model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:JobHosts
 * @description This controller's for the job hosts page
*/


function JobHostSummaryList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobHostList, GenerateList,
    LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, Refresh,
    JobStatusToolTip) {

    ClearScope();

    var list = JobHostList,
        defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_host_summaries/',
        view = GenerateList,
        inventory;

    $scope.job_id = $routeParams.id;
    $scope.host_id = null;

    // After a refresh, populate any needed summary field values on each row
    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {

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

        for (var i = 0; i < $scope.jobhosts.length; i++) {
            $scope.jobhosts[i].hostLinkTo = '/#/inventories/' + inventory + '/?host_name=' +
                encodeURI($scope.jobhosts[i].summary_fields.host.name);
        }
    });

    if ($scope.removeJobReady) {
        $scope.removeJobReady();
    }
    $scope.removeJobReady = $scope.$on('JobReady', function() {
        view.inject(list, { mode: 'edit', scope: $scope });

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
    });

    Rest.setUrl(GetBasePath('jobs') + $scope.job_id);
    Rest.get()
        .success(function (data) {
            inventory = data.inventory;
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
            $scope.$emit('JobReady');
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to get job status for job: ' + $scope.job_id + '. GET status: ' + status
            });
        });

    $scope.showEvents = function (host_name, last_job) {
        // When click on !Failed Events link, redirect to latest job/job_events for the host
        Rest.setUrl(last_job);
        Rest.get()
            .success(function (data) {
                $location.url('/jobs_events/' + data.id + '/?host=' + encodeURI(host_name));
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to lookup last job: ' + last_job +
                    '. GET status: ' + status });
            });
    };

    $scope.refresh = function () {
        $scope.search(list.iterator);
    };

}

JobHostSummaryList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobHostList',
    'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'Refresh', 'JobStatusToolTip', 'Wait'
];