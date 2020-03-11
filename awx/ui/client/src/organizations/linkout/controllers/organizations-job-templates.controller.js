/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$stateParams', 'Rest', 'GetBasePath', '$state', 'OrgJobTemplateList', 'OrgJobTemplateDataset',
    function($scope, $stateParams, Rest, GetBasePath, $state, OrgJobTemplateList, Dataset) {

        var list = OrgJobTemplateList,
            orgBase = GetBasePath('organizations');

        $scope.$on(`ws-jobs`, function (e, msg) {
            if (msg.unified_job_template_id && $scope[list.name]) {
                const template = $scope[list.name].find((t) => t.id === msg.unified_job_template_id);
                if (template) {
                    if (msg.status === 'pending') {
                        // This is a new job - add it to the front of the
                        // recent_jobs array
                        if (template.summary_fields.recent_jobs.length === 10) {
                            template.summary_fields.recent_jobs.pop();
                        }
    
                        template.summary_fields.recent_jobs.unshift({
                            id: msg.unified_job_id,
                            status: msg.status,
                            type: msg.type
                        });
                    } else {
                        // This is an update to an existing job.  Check to see
                        // if we have it in our array of recent_jobs
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
                    }
                }
            }
        });

        init();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .then(({data}) => {
                    $scope.organization_name = data.name;
                    $scope.name = data.name;
                    $scope.org_id = data.id;

                    $scope.orgRelatedUrls = data.related;
                });
        }

        $scope.$on(`${list.iterator}_options`, function(event, data){
            $scope.options = data.data.actions.GET;
            optionsRequestDataProcessing();
        });

        $scope.$watchCollection(`${$scope.list.name}`, function() {
                optionsRequestDataProcessing();
            }
        );
        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            $scope[list.name].forEach(function(item, item_idx) {
                var itm = $scope[list.name][item_idx];

                // Set the item type label
                if (list.fields.type && $scope.options && $scope.options.hasOwnProperty('type')) {
                    $scope.options.type.choices.forEach(function(choice) {
                        if (choice[0] === item.type) {
                            itm.type_label = choice[1];
                        }
                    });
                }
            });
        }

        $scope.editJobTemplate = function(id) {
            $state.go('templates.editJobTemplate', { job_template_id: id });
        };
    }
];
