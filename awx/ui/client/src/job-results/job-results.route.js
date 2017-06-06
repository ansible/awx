/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

const defaultParams = {
    page_size: "200",
    order_by: 'start_line',
    not__event__in: 'playbook_on_start,playbook_on_play_start,playbook_on_task_start,playbook_on_stats'
};

export default {
    name: 'jobResult',
    url: '/jobs/{id: int}',
    searchPrefix: 'job_event',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: '{{ job.id }} - {{ job.name }}'
    },
    data: {
        socket: {
            "groups":{
                "jobs": ["status_changed", "summary"],
                "job_events": []
            }
        }
    },
    params: {
        job_event_search: {
            value: defaultParams,
            dynamic: true,
            squash: ''
        }
    },
    resolve: {
        statusSocket: ['$rootScope', '$stateParams', function($rootScope, $stateParams) {
            var preScope = {};
            var eventOn = $rootScope.$on(`ws-jobs`, function(e, data) {
                if (parseInt(data.unified_job_id, 10) ===
                    parseInt($stateParams.id,10)) {
                    preScope.job_status = data.status;
                }
            });
            return [preScope, eventOn];
        }],
        // the GET for the particular job
        jobData: ['Rest', 'GetBasePath', '$stateParams', '$q', '$state', 'Alert', 'jobResultsService', function(Rest, GetBasePath, $stateParams, $q, $state, Alert, jobResultsService) {
            return jobResultsService.getJobData($stateParams.id);
        }],
        Dataset: ['QuerySet', '$stateParams', 'jobData',
            function(qs, $stateParams, jobData) {
                let path = jobData.related.job_events;
                return qs.search(path, $stateParams[`job_event_search`]);
            }
        ],
        // used to signify if job is completed or still running
        jobFinished: ['jobData', function(jobData) {
            if (jobData.finished) {
                return true;
            } else {
                return false;
            }
        }],
        // after the GET for the job, this helps us keep the status bar from
        // flashing as rest data comes in.  If the job is finished and
        // there's a playbook_on_stats event, go ahead and resolve the count
        // so you don't get that flashing!
        count: ['jobData', 'jobResultsService', 'Rest', '$q', '$stateParams', '$state', function(jobData, jobResultsService, Rest, $q, $stateParams, $state) {
            var defer = $q.defer();
            if (jobData.finished) {
                // if the job is finished, grab the playbook_on_stats
                // role to get the final count
                Rest.setUrl(jobData.related.job_events +
                    "?event=playbook_on_stats");
                Rest.get()
                    .success(function(data) {
                        if(!data.results[0]){
                            defer.resolve({val: {
                                ok: 0,
                                skipped: 0,
                                unreachable: 0,
                                failures: 0,
                                changed: 0
                            }, countFinished: false});
                        }
                        else {
                            defer.resolve({
                                val: jobResultsService
                                    .getCountsFromStatsEvent(data
                                        .results[0].event_data),
                                countFinished: true});
                        }
                    })
                    .error(function() {
                        defer.resolve({val: {
                            ok: 0,
                            skipped: 0,
                            unreachable: 0,
                            failures: 0,
                            changed: 0
                        }, countFinished: false});
                    });
            } else {
                // make sure to not include any extra
                // search params for a running job (because we can't filter
                // incoming job events)
                if (!_.isEqual($stateParams.job_event_search, defaultParams)) {
                    let params = _.cloneDeep($stateParams);
                    params.job_event_search = defaultParams;
                    $state.go('.', params, { reload: true });
                }

                // job isn't finished so just send an empty count and read
                // from events
                defer.resolve({val: {
                    ok: 0,
                    skipped: 0,
                    unreachable: 0,
                    failures: 0,
                    changed: 0
                }, countFinished: false});
            }
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
        // OPTIONS request for the job.  Used to make things like the
        // verbosity data in the left-hand pane prettier than just an
        // integer
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
        }],
        jobExtraCredentials: ['Rest', 'GetBasePath', '$stateParams', '$q', function(Rest, GetBasePath, $stateParams, $q) {
            Rest.setUrl(GetBasePath('jobs') + $stateParams.id + '/extra_credentials');
            var val = $q.defer();
            Rest.get()
                .then(function(res) {
                    val.resolve(res.data.results);
                }, function(res) {
                    val.reject(res);
                });
            return val.promise;
        }]
    },
    templateUrl: templateUrl('job-results/job-results'),
    controller: 'jobResultsController'
};
