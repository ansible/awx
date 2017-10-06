'use strict';
import moment from 'moment';

describe('Controller: jobResultsController', () => {
    // Setup
    let jobResultsController;

    let jobData, jobDataOptions, jobLabels, jobFinished, count, $scope, ParseTypeChange, ParseVariableString, jobResultsService, eventQueue, $compile, eventResolve, populateResolve, $rScope, q, $log, Dataset, Rest, $state, QuerySet, i18n,fieldChoices, fieldLabels, $interval, workflowResultsService, statusSocket, jobExtraCredentials;

    statusSocket = function() {
        var fn = function() {};
        return fn;
    };
    jobData = {
        related: {},
        summary_fields: {
            inventory: {
                id: null,
                kind: ''
            }
        }
    };
    jobDataOptions = {
        actions: {
            get: {}
        }
    };
    jobLabels = {};
    jobFinished = true;
    count = {
        val: {},
        countFinished: false
    };
    eventResolve = {
        results: []
    };
    populateResolve = {};

    Dataset = {
        data: {foo: "bar"}
    };

    let provideVals = () => {
        angular.mock.module('jobResults', ($provide) => {
            ParseTypeChange = jasmine.createSpy('ParseTypeChange');
            ParseVariableString = jasmine.createSpy('ParseVariableString');
            jobResultsService = jasmine.createSpyObj('jobResultsService', [
                'deleteJob',
                'cancelJob',
                'relaunchJob',
                'getEvents',
                'getJobData',
            ]);
            eventQueue = jasmine.createSpyObj('eventQueue', [
                'populate',
                'markProcessed',
                'initialize'
            ]);

            Rest = jasmine.createSpyObj('Rest', [
                'setUrl',
                'get'
            ]);

            $state = jasmine.createSpyObj('$state', [
                'reload'
            ]);

            QuerySet = jasmine.createSpyObj('QuerySet', [
                'encodeQueryset'
            ]);

            i18n = {
                _: function(txt) {
                    return txt;
                }
            };

            $provide.service('workflowResultsService', () => {
                return jasmine.createSpyObj('workflowResultsService', ['createOneSecondTimer', 'destroyTimer']);
            });

            $provide.value('statusSocket', statusSocket);

            $provide.value('jobData', jobData);
            $provide.value('jobDataOptions', jobDataOptions);
            $provide.value('jobLabels', jobLabels);
            $provide.value('jobFinished', jobFinished);
            $provide.value('count', count);
            $provide.value('ParseTypeChange', ParseTypeChange);
            $provide.value('ParseVariableString', ParseVariableString);
            $provide.value('jobResultsService', jobResultsService);
            $provide.value('eventQueue', eventQueue);
            $provide.value('Dataset', Dataset);
            $provide.value('Rest', Rest);
            $provide.value('$state', $state);
            $provide.value('QuerySet', QuerySet);
            $provide.value('i18n', i18n);
            $provide.value('fieldChoices', fieldChoices);
            $provide.value('fieldLabels', fieldLabels);
            $provide.value('jobExtraCredentials', jobExtraCredentials);
        });
    };

    let injectVals = () => {
        angular.mock.inject((_jobData_, _jobDataOptions_, _jobLabels_, _jobFinished_, _count_, _ParseTypeChange_, _ParseVariableString_, _jobResultsService_, _eventQueue_, _$compile_, $rootScope, $controller, $q, $httpBackend, _$log_, _Dataset_, _Rest_, _$state_, _QuerySet_, _$interval_, _workflowResultsService_, _statusSocket_) => {
            // when you call $scope.$apply() (which you need to do to
            // to get inside of .then blocks to test), something is
            // causing a request for all static files.
            //
            // this is a hack to just pass those requests through
            //
            // from googling this is probably due to angular-router
            // weirdness
            $httpBackend.when("GET", (url) => (url
                .indexOf("/static/") !== -1))
                .respond('');

            $httpBackend
                .whenGET('/api')
                .respond(200, '');

            $scope = $rootScope.$new();
            $rScope = $rootScope;
            q = $q;
            jobData = _jobData_;
            jobDataOptions = _jobDataOptions_;
            jobLabels = _jobLabels_;
            jobFinished = _jobFinished_;
            count = _count_;
            ParseTypeChange = _ParseTypeChange_;
            ParseVariableString = _ParseVariableString_;
            ParseVariableString.and.returnValue(jobData.extra_vars);
            jobResultsService = _jobResultsService_;
            eventQueue = _eventQueue_;
            $log = _$log_;
            Dataset = _Dataset_;
            Rest = _Rest_;
            $state = _$state_;
            QuerySet = _QuerySet_;
            $interval = _$interval_;
            workflowResultsService = _workflowResultsService_;
            statusSocket = _statusSocket_;

            jobResultsService.getEvents.and
                .returnValue(eventResolve);
            eventQueue.populate.and
                .returnValue(populateResolve);

            jobResultsService.getJobData = function() {
                var deferred = $q.defer();
                deferred.resolve({});
                return deferred.promise;
            };

            $compile = _$compile_;

            jobResultsController = $controller('jobResultsController', {
                $scope: $scope,
                jobData: jobData,
                jobDataOptions: jobDataOptions,
                jobLabels: jobLabels,
                jobFinished: jobFinished,
                count: count,
                ParseTypeChange: ParseTypeChange,
                jobResultsService: jobResultsService,
                eventQueue: eventQueue,
                $compile: $compile,
                $log: $log,
                $q: q,
                Dataset: Dataset,
                Rest: Rest,
                $state: $state,
                QuerySet: QuerySet,
                statusSocket: statusSocket
            });
        });
    };

    beforeEach(angular.mock.module('shared'));

    let bootstrapTest = () => {
        provideVals();
        injectVals();
    };

    describe('bootstrap resolve values on scope', () => {
        beforeEach(() => {
            bootstrapTest();
        });

        it('should set values to scope based on resolve', () => {
            expect($scope.job).toBe(jobData);
            expect($scope.jobOptions).toBe(jobDataOptions.actions.GET);
            expect($scope.labels).toBe(jobLabels);
        });
    });

    describe('getLinks()', () => {
        beforeEach(() => {
            jobData.related = {
                "created_by": "api/v2/users/12",
                "inventory": "api/v2/inventories/12",
                "project": "api/v2/projects/12",
                "credential": "api/v2/credentials/12",
                "cloud_credential": "api/v2/credentials/13",
                "network_credential": "api/v2/credentials/14",
            };

            jobData.summary_fields.inventory = {
                id: 12,
                kind: ''
            };

            bootstrapTest();
        });

        it('should transform related links and set to scope var', () => {
            expect($scope.created_by_link).toBe('/#/users/12');
            expect($scope.inventory_link).toBe('/#/inventories/inventory/12');
            expect($scope.project_link).toBe('/#/projects/12');
            expect($scope.machine_credential_link).toBe('/#/credentials/12');
            expect($scope.cloud_credential_link).toBe('/#/credentials/13');
            expect($scope.network_credential_link).toBe('/#/credentials/14');
        });
    });

    describe('getLabels()', () => {
        beforeEach(() => {
            jobDataOptions.actions.GET = {
                status: {
                    choices: [
                        ["new",
                        "New"]
                    ]
                },
                job_type: {
                    choices: [
                        ["job",
                        "Playbook Run"]
                    ]
                },
                verbosity: {
                    choices: [
                        [0,
                        "0 (Normal)"]
                    ]
                }
            };
            jobData.status = "new";
            jobData.job_type = "job";
            jobData.verbosity = 0;

            bootstrapTest();
        });

        it('should set scope variables based on options', () => {
            $scope.job_status = jobData.status;

            $scope.$apply();
            expect($scope.status_label).toBe("New");
            expect($scope.type_label).toBe("Playbook Run");
            expect($scope.verbosity_label).toBe("0 (Normal)");
        });
    });

    describe('elapsed timer', () => {
        describe('job running', () => {
            beforeEach(() => {
                jobData.started = moment();
                jobData.status = 'running';

                bootstrapTest();
            });

            it('should start timer', () => {
                expect(workflowResultsService.createOneSecondTimer).toHaveBeenCalled();
            });
        });

        describe('job waiting', () => {
            beforeEach(() => {
                jobData.started = null;
                jobData.status = 'waiting';

                bootstrapTest();
            });

            it('should not start timer', () => {
                expect(workflowResultsService.createOneSecondTimer).not.toHaveBeenCalled();
            });
        });

        describe('job transitions to running', () => {
            beforeEach(() => {
                jobData.started = null;
                jobData.status = 'waiting';
                jobData.id = 13;

                bootstrapTest();

                $rScope.$broadcast('ws-jobs', { unified_job_id: jobData.id, status: 'running' });
            });

            it('should start timer', () => {
                expect(workflowResultsService.createOneSecondTimer).toHaveBeenCalled();
            });

            describe('job transitions from running to finished', () => {
                it('should cleanup timer', () => {
                    $rScope.$broadcast('ws-jobs', { unified_job_id: jobData.id, status: 'successful' });
                    expect(workflowResultsService.destroyTimer).toHaveBeenCalled();
                });
            });
        });
    });

    describe('extra vars stuff', () => {
        let extraVars = "foo";

        beforeEach(() => {
            jobData.extra_vars = extraVars;

            bootstrapTest();
        });

        it('should have extra vars on scope', () => {
            expect($scope.job.extra_vars).toBe(extraVars);
        });

        it('should call ParseVariableString and set to scope', () => {
            expect(ParseVariableString)
                .toHaveBeenCalledWith(extraVars);
            expect($scope.variables).toBe(extraVars);
        });

        it('should set the parse type to yaml', () => {
            expect($scope.parseType).toBe('yaml');
        });

        it('should call ParseTypeChange with proper params', () => {
            let params = {
                scope: $scope,
                field_id: 'pre-formatted-variables',
                readOnly: true
            };

            expect(ParseTypeChange)
                .toHaveBeenCalledWith(params);
        });
    });

    describe('$scope.toggleStdoutFullscreen', () => {
        beforeEach(() => {
            bootstrapTest();
        });

        it('should toggle $scope.stdoutFullScreen', () => {
            // essentially set to false
            expect($scope.stdoutFullScreen).toBe(false);

            // toggle once to true
            $scope.toggleStdoutFullscreen();
            expect($scope.stdoutFullScreen).toBe(true);

            // toggle again to false
            $scope.toggleStdoutFullscreen();
            expect($scope.stdoutFullScreen).toBe(false);
        });
    });

    describe('$scope.deleteJob', () => {
        beforeEach(() => {
            bootstrapTest();
        });

        it('should delete the job', () => {
            let job = $scope.job;
            $scope.deleteJob();
            expect(jobResultsService.deleteJob).toHaveBeenCalledWith(job);
        });
    });

    describe('$scope.cancelJob', () => {
        beforeEach(() => {
            bootstrapTest();
        });

        it('should cancel the job', () => {
            let job = $scope.job;
            $scope.cancelJob();
            expect(jobResultsService.cancelJob).toHaveBeenCalledWith(job);
        });
    });

    describe('$scope.relaunchJob', () => {
        beforeEach(() => {
            bootstrapTest();
        });

        it('should relaunch the job', () => {
            let scope = $scope;
            $scope.relaunchJob();
            expect(jobResultsService.relaunchJob)
                .toHaveBeenCalledWith(scope);
        });
    });

    describe('count stuff', () => {
        beforeEach(() => {
            count = {
                val: {
                    ok: 1,
                    skipped: 2,
                    unreachable: 3,
                    failures: 4,
                    changed: 5
                },
                countFinished: true
            };

            bootstrapTest();
        });

        it('should set count values to scope', () => {
            expect($scope.count).toBe(count.val);
            expect($scope.countFinished).toBe(true);
        });

        it('should find the hostCount based on the count', () => {
            expect($scope.hostCount).toBe(15);
        });
    });

    describe('follow stuff - incomplete', () => {
        beforeEach(() => {
            jobFinished = false;

            bootstrapTest();
        });

        it('should set followEngaged based on jobFinished incomplete', () => {
            expect($scope.followEngaged).toBe(true);
        });

        it('should set followTooltip based on jobFinished incomplete', () => {
            expect($scope.followTooltip).toBe("Currently following standard out as it comes in.  Click to unfollow.");
        });
    });

    describe('follow stuff - finished', () => {
        beforeEach(() => {
            jobFinished = true;

            bootstrapTest();
        });

        it('should set followEngaged based on jobFinished', () => {
            expect($scope.followEngaged).toBe(false);
        });

        it('should set followTooltip based on jobFinished', () => {
            expect($scope.followTooltip).toBe("Jump to last line of standard out.");
        });
    });

    describe('event stuff', () => {
        beforeEach(() => {
            jobData.id = 1;
            jobData.related.job_events = "url";

            bootstrapTest();
        });

        xit('should make a rest call to get already completed events', () => {
            expect(jobResultsService.getEvents).toHaveBeenCalledWith("url");
        });

        xit('should call processEvent when receiving message', () => {
            let eventPayload = {"foo": "bar"};
            $rScope.$broadcast('ws-job_events-1', eventPayload);
            expect(eventQueue.populate).toHaveBeenCalledWith(eventPayload);
        });

        it('should set the job status on scope when receiving message', () => {
            let eventPayload = {
                unified_job_id: 1,
                status: 'finished'
            };
            $rScope.$broadcast('ws-jobs', eventPayload);
            expect($scope.job_status).toBe(eventPayload.status);
        });
    });

    describe('getEvents and populate stuff', () => {
        describe('getEvents', () => {
            let event1 = {
                event: 'foo'
            };

            let event2 = {
                event_name: 'bar'
            };

            let event1Processed = {
                event_name: 'foo'
            };

            beforeEach(() => {
                eventResolve = {
                    results: [
                        event1,
                        event2
                    ]
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('should change the event name to event_name', () => {
                expect(eventQueue.populate)
                    .toHaveBeenCalledWith(event1Processed);
            });

            xit('should pass through the event with event_name', () => {
                expect(eventQueue.populate)
                    .toHaveBeenCalledWith(event2);
            });

            xit('should have called populate twice', () => {
                expect(eventQueue.populate.calls.count()).toEqual(2);
            });

            // TODO: can't figure out how to a test of events.next...
            // if you set events.next to true it causes the tests to
            // stop running
        });

        describe('populate - start time', () => {
            beforeEach(() => {
                jobData.start = "";

                populateResolve = {
                    startTime: 'foo',
                    changes: ['startTime']
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('sets start time when passed as a change', () => {
                expect($scope.job.start).toBe('foo');
            });
        });

        describe('populate - start time already set', () => {
            beforeEach(() => {
                jobData.start = "bar";

                populateResolve = {
                    startTime: 'foo',
                    changes: ['startTime']
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('does not set start time because already set', () => {
                expect($scope.job.start).toBe('bar');
            });
        });

        describe('populate - count already received', () => {
            let receiveCount = {
                ok: 2,
                skipped: 2,
                unreachable: 2,
                failures: 2,
                changed: 2
            };

            let alreadyCount = {
                ok: 3,
                skipped: 3,
                unreachable: 3,
                failures: 3,
                changed: 3
            };

            beforeEach(() => {
                count.countFinished = true;
                count.val = alreadyCount;

                populateResolve = {
                    count: receiveCount,
                    changes: ['count']
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('count does not change', () => {
                expect($scope.count).toBe(alreadyCount);
                expect($scope.hostCount).toBe(15);
            });
        });

        describe('populate - playCount, taskCount and countFinished', () => {
            beforeEach(() => {

                populateResolve = {
                    playCount: 12,
                    taskCount: 13,
                    changes: ['playCount', 'taskCount', 'countFinished']
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('sets playCount', () => {
                expect($scope.playCount).toBe(12);
            });

            xit('sets taskCount', () => {
                expect($scope.taskCount).toBe(13);
            });

            xit('sets countFinished', () => {
                expect($scope.countFinished).toBe(true);
            });
        });

        describe('populate - finishedTime', () => {
            beforeEach(() => {
                jobData.finished = "";

                populateResolve = {
                    finishedTime: "finished_time",
                    changes: ['finishedTime']
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('sets finished time and changes follow tooltip', () => {
                expect($scope.job.finished).toBe('finished_time');
                expect($scope.jobFinished).toBe(true);
                expect($scope.followTooltip)
                    .toBe("Jump to last line of standard out.");
            });
        });

        describe('populate - finishedTime when already finished', () => {
            beforeEach(() => {
                jobData.finished = "already_set";

                populateResolve = {
                    finishedTime: "finished_time",
                    changes: ['finishedTime']
                };

                bootstrapTest();

                $scope.$apply();
            });

            xit('does not set finished time because already set', () => {
                expect($scope.job.finished).toBe('already_set');
                expect($scope.jobFinished).toBe(true);
                expect($scope.followTooltip)
                    .toBe("Jump to last line of standard out.");
            });
        });

        describe('populate - stdout', () => {
            beforeEach(() => {

                populateResolve = {
                    counter: 12,
                    stdout: "line",
                    changes: ['stdout']
                };

                bootstrapTest();

                spyOn($log, 'error');

                $scope.followEngaged = true;

                $scope.$apply();
            });

            xit('creates new child scope for the event', () => {
                expect($scope.events[12].event).toBe(populateResolve);

                // in unit test, followScroll should not be defined as
                // directive has not been instantiated
                expect($log.error).toHaveBeenCalledWith("follow scroll undefined, standard out directive not loaded yet?");
            });
        });
    });
});
