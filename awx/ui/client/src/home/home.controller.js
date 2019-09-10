/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope','Wait', '$timeout', 'i18n',
    'Rest', 'GetBasePath', 'ProcessErrors', 'graphData',
    function($scope, Wait, $timeout, i18n,
    Rest, GetBasePath, ProcessErrors, graphData) {

        var dataCount = 0;
        let launchModalOpen = false;
        let refreshAfterLaunchClose = false;
        let pendingRefresh = false;
        let refreshTimerRunning = false;

        $scope.$on('ws-jobs', function () {
            if (!launchModalOpen) {
                if (!refreshTimerRunning) {
                    refreshLists();
                } else {
                    pendingRefresh = true;
                }
            } else {
                refreshAfterLaunchClose = true;
            }
        });

        $scope.$on('launchModalOpen', (evt, isOpen) => {
            evt.stopPropagation();
            if (!isOpen && refreshAfterLaunchClose) {
                refreshAfterLaunchClose = false;
                refreshLists();
            }
            launchModalOpen = isOpen;
        });

        if ($scope.removeDashboardDataLoadComplete) {
            $scope.removeDashboardDataLoadComplete();
        }
        $scope.removeDashboardDataLoadComplete = $scope.$on('dashboardDataLoadComplete', function () {
            dataCount++;
            if (dataCount === 3) {
                Wait("stop");
                dataCount = 0;
            }
        });

        if ($scope.removeDashboardReady) {
            $scope.removeDashboardReady();
        }
        $scope.removeDashboardReady = $scope.$on('dashboardReady', function (e, data) {
            $scope.dashboardCountsData = data;
            $scope.graphData = graphData;
            $scope.graphData.period = "month";
            $scope.graphData.jobType = "all";
            $scope.graphData.status = "both";
            $scope.$emit('dashboardDataLoadComplete');
        });

        if ($scope.removeDashboardJobsListReady) {
            $scope.removeDashboardJobsListReady();
        }
        $scope.removeDashboardJobsListReady = $scope.$on('dashboardJobsListReady', function (e, data) {
            $scope.dashboardJobsListData = data;
            $scope.$emit('dashboardDataLoadComplete');
        });

        if ($scope.removeDashboardJobTemplatesListReady) {
            $scope.removeDashboardJobTemplatesListReady();
        }
        $scope.removeDashboardJobTemplatesListReady = $scope.$on('dashboardJobTemplatesListReady', function (e, data) {
            $scope.dashboardJobTemplatesListData = data;
            $scope.$emit('dashboardDataLoadComplete');
        });

        function refreshLists () {
            Rest.setUrl(GetBasePath('dashboard'));
            Rest.get()
            .then(({data}) => {
                $scope.dashboardData = data;
            })
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard host graph data: ${status}`) });
            });

            Rest.setUrl(GetBasePath("unified_jobs") + "?order_by=-finished&page_size=5&finished__isnull=false&type=workflow_job,job&count_disabled=1");
            Rest.setHeader({'X-WS-Session-Quiet': true});
            Rest.get()
            .then(({data}) => {
                $scope.dashboardJobsListData = data.results;
            })
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard jobs list: ${status}`) });
            });

            Rest.setUrl(GetBasePath("unified_job_templates") + "?order_by=-last_job_run&page_size=5&last_job_run__isnull=false&type=workflow_job_template,job_template&count_disabled=1");
            Rest.get()
            .then(({data}) => {
                $scope.dashboardJobTemplatesListData = data.results;
            })
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard jobs list: ${status}`) });
            });

            if ($scope.graphData) {
                Rest.setUrl(`${GetBasePath('dashboard')}graphs/jobs/?period=${$scope.graphData.period}&job_type=${$scope.graphData.jobType}`);
                Rest.setHeader({'X-WS-Session-Quiet': true});
                Rest.get()
                .then(function(value) {
                    if($scope.graphData.status === "successful" || $scope.graphData.status === "failed"){
                        delete value.data.jobs[$scope.graphData.status];
                    }
                    $scope.graphData.jobStatus = value.data;
                })
                .catch(function({data, status}) {
                    ProcessErrors(null, data, status,  null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard graph data: ${status}`)});
                });
            }

            pendingRefresh = false;
            refreshTimerRunning = true;
            $timeout(() => {
                if (pendingRefresh) {
                    refreshLists();
                } else {
                    refreshTimerRunning = false;
                }
            }, 5000);
        }

        Wait('start');
        Rest.setUrl(GetBasePath('dashboard'));
        Rest.get()
        .then(({data}) => {
            $scope.dashboardData = data;
            $scope.$emit('dashboardReady', data);
        })
        .catch(({data, status}) => {
            ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard: ${status}`) });
        });
        Rest.setUrl(GetBasePath("unified_jobs") + "?order_by=-finished&page_size=5&finished__isnull=false&type=workflow_job,job&count_disabled=1");
        Rest.setHeader({'X-WS-Session-Quiet': true});
        Rest.get()
        .then(({data}) => {
            data = data.results;
            $scope.$emit('dashboardJobsListReady', data);
        })
        .catch(({data, status}) => {
            ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard jobs list: ${status}`) });
        });
        Rest.setUrl(GetBasePath("unified_job_templates") + "?order_by=-last_job_run&page_size=5&last_job_run__isnull=false&type=workflow_job_template,job_template");
        Rest.get()
        .then(({data}) => {
            data = data.results;
            $scope.$emit('dashboardJobTemplatesListReady', data);
        })
        .catch(({data, status}) => {
            ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard job templates list: ${status}`) });
        });

    }
];
