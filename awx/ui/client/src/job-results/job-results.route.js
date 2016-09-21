/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail',
    url: '/jobs/:id',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: '{{ job.id }} - {{ job.name }}'
    },
    resolve: {
        jobData: ['Rest', 'GetBasePath', '$stateParams', '$q', '$state', 'Alert', function(Rest, GetBasePath, $stateParams, $q, $state, Alert) {
            Rest.setUrl(GetBasePath('jobs') + $stateParams.id);
            var val = $q.defer();
            Rest.get()
                .then(function(data) {
                    val.resolve(data.data);
                }, function(data) {
                    val.reject(data);

                    if (data.status === 404) {
                        Alert('Job Not Found', 'Cannot find job.', 'alert-info');
                    } else if (data.status === 403) {
                        Alert('Insufficient Permissions', 'You do not have permission to view this job.', 'alert-info');
                    }

                    $state.go('jobs');
                });
            return val.promise;
        }],
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

            Rest.setUrl(GetBasePath('jobs') + $stateParams.id + '/labels/');
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
        jobDataOptions: ['Rest', 'GetBasePath', '$stateParams', '$q', function(Rest, GetBasePath, $stateParams, $q) {
            Rest.setUrl(GetBasePath('jobs') + $stateParams.id);
            var val = $q.defer();
            Rest.options()
                .then(function(data) {
                    val.resolve(data.data);
                }, function(data) {
                    val.reject(data);
                });
            return val.promise;
        }]
    },
    templateUrl: templateUrl('job-results/job-results'),
    controller: ['jobData', 'jobDataOptions', 'jobLabels', '$scope', 'ParseTypeChange', 'ParseVariableString', function(jobData, jobDataOptions, jobLabels, $scope, ParseTypeChange, ParseVariableString) {

        var getTowerLinks = function() {
            var getTowerLink = function(key) {
                if ($scope.job.related[key]) {
                    return '/#/' + $scope.job.related[key]
                        .split('api/v1/')[1];
                } else {
                    return null;
                }
            };

            $scope.job_template_link = getTowerLink('job_template');
            $scope.created_by_link = getTowerLink('created_by');
            $scope.inventory_link = getTowerLink('inventory');
            $scope.project_link = getTowerLink('project');
            $scope.machine_credential_link = getTowerLink('credential');
            $scope.cloud_credential_link = getTowerLink('cloud_credential');
            $scope.network_credential_link = getTowerLink('network_credential');
        };

        var getTowerLabels = function() {
            var getTowerLabel = function(key) {
                if ($scope.jobOptions && $scope.jobOptions[key]) {
                    return $scope.jobOptions[key].choices
                        .filter(val => val[0] === $scope.job[key])
                        .map(val => val[1])[0];
                } else {
                    return null;
                }
            };

            $scope.status_label = getTowerLabel('status');
            $scope.type_label = getTowerLabel('job_type');
            $scope.verbosity_label = getTowerLabel('verbosity');
        };

        // put initially resolved request data on scope
        $scope.job = jobData;
        $scope.jobOptions = jobDataOptions.actions.GET;
        $scope.labels = jobLabels;

        // turn related api browser routes into tower routes
        getTowerLinks();

        // use options labels to manipulate display of details
        getTowerLabels();

        // set up a read only code mirror for extra vars
        $scope.variables = ParseVariableString($scope.job.extra_vars);
        $scope.parseType = 'yaml';
        ParseTypeChange({ scope: $scope,
            field_id: 'pre-formatted-variables',
            readOnly: true });
    }]
};
