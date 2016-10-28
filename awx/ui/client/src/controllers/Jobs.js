/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Jobs
 * @description This controller's for the jobs page
 */



export function JobsListController($state, $rootScope, $log, $scope, $compile, $stateParams,
    ClearScope, Find, DeleteJob, RelaunchJob, AllJobsList, ScheduledJobsList, GetBasePath, Dataset) {

    ClearScope();

    var list = AllJobsList;

    init();

    function init() {
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $scope.showJobType = true;

        _.forEach($scope[list.name], buildTooltips);
    }

    function buildTooltips(job) {
        job.status_tip = 'Job ' + job.status + ". Click for details.";
    }

    $scope.deleteJob = function(id) {
        DeleteJob({ scope: $scope, id: id });
    };

    $scope.relaunchJob = function(event, id) {
        var list, job, typeId;
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            //ignore
        }

        job = Find({ list: list, key: 'id', val: id });
        if (job.type === 'inventory_update') {
            typeId = job.inventory_source;
        } else if (job.type === 'project_update') {
            typeId = job.project;
        } else if (job.type === 'job' || job.type === "system_job" || job.type === 'ad_hoc_command') {
            typeId = job.id;
        }
        RelaunchJob({ scope: $scope, id: typeId, type: job.type, name: job.name });
    };

    $scope.refreshJobs = function() {
        $state.go('.', null, { reload: true });
    };

    $scope.viewJobDetails = function(job) {

        var goToJobDetails = function(state) {
            $state.go(state, { id: job.id }, { reload: true });
        };
        switch (job.type) {
            case 'job':
                goToJobDetails('jobDetail');
                break;
            case 'ad_hoc_command':
                goToJobDetails('adHocJobStdout');
                break;
            case 'system_job':
                goToJobDetails('managementJobStdout');
                break;
            case 'project_update':
                goToJobDetails('scmUpdateStdout');
                break;
            case 'inventory_update':
                goToJobDetails('inventorySyncStdout');
                break;
        }

    };

    $scope.refreshJobs = function() {
        $state.reload();
    };

    if ($rootScope.removeJobStatusChange) {
        $rootScope.removeJobStatusChange();
    }
    $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange-jobs', function() {
        $scope.refreshJobs();
    });

    if ($rootScope.removeScheduleStatusChange) {
        $rootScope.removeScheduleStatusChange();
    }
    $rootScope.removeScheduleStatusChange = $rootScope.$on('ScheduleStatusChange', function() {
        $state.reload();
    });
}

JobsListController.$inject = ['$state', '$rootScope', '$log', '$scope', '$compile', '$stateParams',
    'ClearScope', 'Find', 'DeleteJob', 'RelaunchJob', 'AllJobsList', 'ScheduledJobsList', 'GetBasePath', 'Dataset'
];
