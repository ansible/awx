/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

import workflowResultsController from './workflow-results.controller';

export default {
    name: 'workflowResults',
    url: '/workflows/:id',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: '{{ workflow.id }} - {{ workflow.name }}'
    },
    data: {
        socket: {
            "groups":{
                "jobs": ["status_changed"]
            }
        }
    },
    templateUrl: templateUrl('workflow-results/workflow-results'),
    controller: workflowResultsController,
    resolve: {
        // the GET for the particular workflow
        workflowData: ['Rest', 'GetBasePath', '$stateParams', '$q', '$state', 'Alert', function(Rest, GetBasePath, $stateParams, $q, $state, Alert) {
            Rest.setUrl(GetBasePath('workflow_jobs') + $stateParams.id);
            var defer = $q.defer();
            Rest.get()
                .then(function(data) {
                    defer.resolve(data.data);
                }, function(data) {
                    defer.reject(data);

                    if (data.status === 404) {
                        Alert('Job Not Found', 'Cannot find job.', 'alert-info');
                    } else if (data.status === 403) {
                        Alert('Insufficient Permissions', 'You do not have permission to view this job.', 'alert-info');
                    }

                    $state.go('jobs');
                });
            return defer.promise;
        }],
        // after the GET for the job, this helps us keep the status bar from
        // flashing as rest data comes in. Provides the list of workflow nodes
        workflowNodes: ['workflowData', 'Rest', '$q', function(workflowData, Rest, $q) {
            var defer = $q.defer();
                Rest.setUrl(workflowData.related.workflow_nodes + '?order_by=id');
                Rest.get()
                    .success(function(data) {
                        if(data.next) {
                            let allNodes = data.results;
                            let getNodes = function(nextUrl){
                                // Get the workflow nodes
                                Rest.setUrl(nextUrl);
                                Rest.get()
                                    .success(function(nextData) {
                                        for(var i=0; i<nextData.results.length; i++) {
                                            allNodes.push(nextData.results[i]);
                                        }
                                        if(nextData.next) {
                                            // Get the next page
                                            getNodes(nextData.next);
                                        }
                                        else {
                                            defer.resolve(allNodes);
                                        }
                                });
                            };
                            getNodes(data.next);
                        }
                        else {
                            defer.resolve(data.results);
                        }
                    })
                    .error(function() {
                        // TODO: handle this
                        //defer.resolve(data);
                    });
            return defer.promise;
        }],
        // after the GET for the workflow & it's nodes, this helps us keep the
        // status bar from flashing as rest data comes in.  If the workflow
        //  is finished and there's a playbook_on_stats event, go ahead and
        // resolve the count so you don't get that flashing!
        count: ['workflowData', 'workflowNodes', 'workflowResultsService', 'Rest', '$q', function(workflowData, workflowNodes, workflowResultsService, Rest, $q) {
            var defer = $q.defer();
            defer.resolve({
                val: workflowResultsService
                    .getCounts(workflowNodes),
                        countFinished: true});
            return defer.promise;
        }],
        // GET for the particular jobs labels to be displayed in the
        // left-hand pane
        jobLabels: ['Rest', 'GetBasePath', '$stateParams', '$q', function(Rest, GetBasePath, $stateParams, $q) {
            var getNext = function(data, arr, resolve) {
                Rest.setUrl(data.next);
                Rest.get()
                    .success(function (data) {
                        if (data.next) {
                            getNext(data, arr.concat(data.results), resolve);
                        } else {
                            resolve.resolve(arr.concat(data.results)
                                .map(val => val.name));
                        }
                    });
            };

            var seeMoreResolve = $q.defer();

            Rest.setUrl(GetBasePath('workflow_jobs') + $stateParams.id + '/labels/');
            Rest.get()
                .success(function(data) {
                    if (data.next) {
                        getNext(data, data.results, seeMoreResolve);
                    } else {
                        seeMoreResolve.resolve(data.results
                            .map(val => val.name));
                    }
                });

            return seeMoreResolve.promise;
        }],
        // OPTIONS request for the workflow.  Used to make things like the
        // verbosity data in the left-hand pane prettier than just an
        // integer
        workflowDataOptions: ['Rest', 'GetBasePath', '$stateParams', '$q', function(Rest, GetBasePath, $stateParams, $q) {
            Rest.setUrl(GetBasePath('workflow_jobs') + $stateParams.id);
            var defer = $q.defer();
            Rest.options()
                .then(function(data) {
                    defer.resolve(data.data);
                }, function(data) {
                    defer.reject(data);
                });
            return defer.promise;
        }]
    }

};
