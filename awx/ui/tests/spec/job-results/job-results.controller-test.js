'use strict';

describe('Controller: jobResultsController', () => {
    // Setup
    let jobResultsController;

    let jobData, jobDataOptions, jobLabels, jobFinished, count, $scope, ParseTypeChange, ParseVariableString, jobResultsService, eventQueue, $compile, eventDefer, populateResolve, $rScope;

    jobData = {
        related: {}
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
    eventDefer = {};
    populateResolve = {};

    let provideVals = () => {
        angular.mock.module('jobResults', ($provide) => {
            ParseTypeChange = jasmine.createSpy('ParseTypeChange');
            ParseVariableString = jasmine.createSpy('ParseVariableString');
            jobResultsService = jasmine.createSpyObj('jobResultsService', [
                'deleteJob',
                'cancelJob',
                'relaunchJob',
                'getEvents'
            ]);
            eventQueue = jasmine.createSpyObj('eventQueue', [
                'populate',
                'markProcessed'
            ]);
            $compile = jasmine.createSpy('$compile');

            $provide.value('jobData', jobData);
            $provide.value('jobDataOptions', jobDataOptions);
            $provide.value('jobLabels', jobLabels);
            $provide.value('jobFinished', jobFinished);
            $provide.value('count', count);
            $provide.value('ParseTypeChange', ParseTypeChange);
            $provide.value('ParseVariableString', ParseVariableString);
            $provide.value('jobResultsService', jobResultsService);
            $provide.value('eventQueue', eventQueue);
            $provide.value('$compile', $compile);
        });
    };

    let injectVals = () => {
        angular.mock.inject((_jobData_, _jobDataOptions_, _jobLabels_, _jobFinished_, _count_, _ParseTypeChange_, _ParseVariableString_, _jobResultsService_, _eventQueue_, _$compile_, $rootScope, $controller, $q) => {
            $scope = $rootScope.$new();
            $rScope = $rootScope;
            jobData = _jobData_;
            jobDataOptions = _jobDataOptions_;
            jobLabels = _jobLabels_;
            jobFinished = _jobFinished_;
            count = _count_;
            ParseTypeChange = _ParseTypeChange_;
            ParseVariableString = _ParseVariableString_;
            ParseVariableString.and.returnValue(jobData.extra_vars);
            jobResultsService = _jobResultsService_;

            // TODO: neither one of these and.returnValue's work as
            // expected, gotta figure out how to make these work
            eventDefer = $q.defer();
            jobResultsService.getEvents.and.returnValue($q.when(eventDefer));

            eventQueue = _eventQueue_;
            eventQueue.populate.and.returnValue($q.when(populateResolve));

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
                $compile: $compile
            });
        });
    };

    beforeEach(angular.mock.module('Tower'));

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

    describe('getTowerLinks()', () => {
        beforeEach(() => {
            jobData.related = {
                "job_template": "api/v1/job_templates/12",
                "created_by": "api/v1/users/12",
                "inventory": "api/v1/inventories/12",
                "project": "api/v1/projects/12",
                "credential": "api/v1/credentials/12",
                "cloud_credential": "api/v1/credentials/13",
                "network_credential": "api/v1/credentials/14",
            };

            bootstrapTest();
        });

        it('should transform related links and set to scope var', () => {
            expect($scope.job_template_link).toBe('/#/job_templates/12');
            expect($scope.created_by_link).toBe('/#/users/12');
            expect($scope.inventory_link).toBe('/#/inventories/12');
            expect($scope.project_link).toBe('/#/projects/12');
            expect($scope.machine_credential_link).toBe('/#/credentials/12');
            expect($scope.cloud_credential_link).toBe('/#/credentials/13');
            expect($scope.network_credential_link).toBe('/#/credentials/14');
        });
    });

    describe('getTowerLabels()', () => {
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
            expect($scope.status_label).toBe("New");
            expect($scope.type_label).toBe("Playbook Run");
            expect($scope.verbosity_label).toBe("0 (Normal)");
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

        it('should make a rest call to get already completed events', () => {
            expect(jobResultsService.getEvents).toHaveBeenCalledWith("url");
        });

        it('should call processEvent when receiving message', () => {
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
            expect($scope.job.status).toBe(eventPayload.status);
        });

        // TODO: test getEvents function

        // TODO: test processEvent function
    });
});
