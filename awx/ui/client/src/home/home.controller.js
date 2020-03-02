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
        let pendingDashboardRefresh = false;
        let dashboardTimerRunning = false;
        let newJobsTimerRunning = false;
        let newTemplatesTimerRunning = false;
        let newJobs = [];
        let newTemplates =[];

        const fetchDashboardData = () => {
            Rest.setUrl(GetBasePath('dashboard'));
            Rest.get()
            .then(({data}) => {
                $scope.dashboardData = data;
            })
            .catch(({data, status}) => {
                ProcessErrors($scope, data, status, null, { hdr: i18n._('Error!'), msg: i18n._(`Failed to get dashboard host graph data: ${status}`) });
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

            pendingDashboardRefresh = false;
            dashboardTimerRunning = true;
            $timeout(() => {
                if (pendingDashboardRefresh) {
                    fetchDashboardData();
                } else {
                    dashboardTimerRunning = false;
                }
            }, 5000);
        };

        const fetchNewJobs = () => {
            newJobsTimerRunning = true;
            const newJobIdsFilter = newJobs.join(',');
            newJobs = [];
            Rest.setUrl(`${GetBasePath("unified_jobs")}?id__in=${newJobIdsFilter}&order_by=-finished&finished__isnull=false&type=workflow_job,job&count_disabled=1`);
            Rest.get()
                .then(({ data }) => {
                    const joinedJobs = data.results.concat($scope.dashboardJobsListData);
                    $scope.dashboardJobsListData =
                        joinedJobs.length > 5 ? joinedJobs.slice(0, 5) : joinedJobs;
                    $timeout(() => {
                        if (newJobs.length > 0) {
                            fetchNewJobs();
                        } else {
                            newJobsTimerRunning = false;
                        }
                    }, 5000);
                })
                .catch(({ data, status }) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: i18n._('Error!'),
                        msg: i18n._(`Failed to get new jobs for dashboard: ${status}`)
                    });
                });
        };

        const fetchNewTemplates = () => {
            newTemplatesTimerRunning = true;
            const newTemplateIdsFilter = newTemplates.join(',');
            newTemplates = [];
            Rest.setUrl(`${GetBasePath("unified_job_templates")}?id__in=${newTemplateIdsFilter}&order_by=-last_job_run&last_job_run__isnull=false&type=workflow_job_template,job_template&count_disabled=1"`);
            Rest.get()
                .then(({ data }) => {
                    const joinedTemplates = data.results.concat($scope.dashboardJobTemplatesListData).sort((a, b) => new Date(b.last_job_run) - new Date(a.last_job_run));
                    $scope.dashboardJobTemplatesListData =
                        joinedTemplates.length > 5 ? joinedTemplates.slice(0, 5) : joinedTemplates;
                    $timeout(() => {
                        if (newTemplates.length > 0 && !launchModalOpen) {
                            fetchNewTemplates();
                        } else {
                            newTemplatesTimerRunning = false;
                        }
                    }, 5000);
                })
                .catch(({ data, status }) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: i18n._('Error!'),
                        msg: i18n._(`Failed to get new templates for dashboard: ${status}`)
                    });
                });
        };

        $scope.$on('ws-jobs', function (e, msg) {
            if (msg.status === 'successful' || msg.status === 'failed' || msg.status === 'canceled' || msg.status === 'error') {
                newJobs.push(msg.unified_job_id);
                if (!newJobsTimerRunning) {
                    fetchNewJobs();
                }
                if (!launchModalOpen) {
                    if (!dashboardTimerRunning) {
                        fetchDashboardData();
                    } else {
                        pendingDashboardRefresh = true;
                    }
                } else {
                    refreshAfterLaunchClose = true;
                }
            }

            const template = $scope.dashboardJobTemplatesListData.find((t) => t.id === msg.unified_job_template_id);
            if (template) {
                if (msg.status === 'pending') {
                    if (template.summary_fields.recent_jobs.length === 10) {
                        template.summary_fields.recent_jobs.pop();
                    }

                    template.summary_fields.recent_jobs.unshift({
                        id: msg.unified_job_id,
                        status: msg.status,
                        type: msg.type
                    });
                } else {
                    for (let i=0; i<template.summary_fields.recent_jobs.length; i++) {
                        const recentJob = template.summary_fields.recent_jobs[i];
                        if (recentJob.id === msg.unified_job_id) {
                            recentJob.status = msg.status;
                            if (msg.finished) {
                                recentJob.finished = msg.finished;
                                template.last_job_run = msg.finished;
                            }
                            break;
                        }
                    }

                    if (msg.status === 'successful' || msg.status === 'failed' || msg.status === 'canceled') {
                        $scope.dashboardJobTemplatesListData.sort((a, b) => new Date(b.last_job_run) - new Date(a.last_job_run));
                    }
                }
            } else {
                newTemplates.push(msg.unified_job_template_id);
                if (!launchModalOpen && !newTemplatesTimerRunning) {
                    fetchNewTemplates();
                }
            }
        });

        $scope.$on('launchModalOpen', (evt, isOpen) => {
            evt.stopPropagation();
            if (!isOpen && refreshAfterLaunchClose) {
                refreshAfterLaunchClose = false;
                fetchDashboardData();
                if (newTemplates.length > 0) {
                    fetchNewTemplates();
                }
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
