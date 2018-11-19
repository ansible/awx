'use strict';
import moment from 'moment';
import workflow_job_options_json from './data/workflow_job_options.js';
import workflow_job_json from './data/workflow_job.js';

describe('Controller: workflowResults', () => {
    let $controller;
    let workflowResults;
    let $rootScope;
    let workflowResultsService;
    let $interval;

    let treeData = {
        data: {
            children: []
        }
    };

    beforeEach(angular.mock.module('workflowResults', ($provide) => {
        ['PromptDialog', 'Prompt', 'Wait', 'Rest', '$state', 'ProcessErrors',
         'jobLabels', 'workflowNodes', 'count', 'WorkflowJobModel', 'ComponentsStrings'
        ].forEach((item) => {
            $provide.value(item, {});
        });
        $provide.value('$stateExtender', { addState: jasmine.createSpy('addState'), });
        $provide.value('moment', moment);
        $provide.value('workflowData', workflow_job_json);
        $provide.value('workflowDataOptions', workflow_job_options_json);
        $provide.value('ParseTypeChange', function() {});
        $provide.value('ParseVariableString', function() {});
        $provide.value('i18n', { '_': (a) => { return a; } });
        $provide.provider('$stateProvider', { '$get': function() { return function() {}; } });
        $provide.service('WorkflowChartService', function($q) {
            return {
                generateArraysOfNodesAndLinks: function() {
                    var deferred = $q.defer();
                    deferred.resolve();
                    return deferred.promise;
                }
            };
        });
    }));

    beforeEach(angular.mock.inject(function(_$controller_, _$rootScope_, _workflowResultsService_, _$interval_){
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        workflowResultsService = _workflowResultsService_;
        $interval = _$interval_;
    }));

    describe('elapsed timer', () => {
        let scope;

        beforeEach(() => {
            scope = $rootScope.$new();
            spyOn(workflowResultsService, 'createOneSecondTimer').and.callThrough();
            spyOn(workflowResultsService, 'destroyTimer').and.callThrough();
        });


        function jobWaitingWorkflowResultsControllerFixture(started, status) {
            workflow_job_json.started = started;
            workflow_job_json.status = status;
            workflowResults = $controller('workflowResultsController', {
                $scope: scope,
                $rootScope: $rootScope,
            });
        }

        describe('init()', () => {
            describe('job running', () => {
                beforeEach(() => {
                    jobWaitingWorkflowResultsControllerFixture(moment(), 'running');
                });

                // Note: Ensuring the outside service method is called to create a timer may
                // be overkill. Especially since we validate the side effect in the next test.
                it('should call to start timer on load when job is already running', () => {
                    expect(workflowResultsService.createOneSecondTimer).toHaveBeenCalled();
                    expect(workflowResultsService.createOneSecondTimer.calls.argsFor(0)[0]).toBe(workflow_job_json.started);
                });

                it('should set update scope var with elapsed time', () => {
                    $interval.flush(10 * 1000);

                    // TODO: mock moment() so when we fast-forward time with $interval
                    // the system clocks seems to fast forward too.
                    //expect(scope.workflow.elapsed).toBe(10);
                });

                it('should call to destroy timer on destroy', () => {
                    scope.$destroy();
                    expect(workflowResultsService.destroyTimer).toHaveBeenCalled();
                    expect(workflowResultsService.destroyTimer.calls.argsFor(0)[0]).not.toBe(null);
                });
            });

            describe('job waiting', () => {
                beforeEach(() => {
                    jobWaitingWorkflowResultsControllerFixture(null, 'waiting');
                });

                it('should not start elapsed timer', () => {
                    expect(workflowResultsService.createOneSecondTimer).not.toHaveBeenCalled();
                });

            });

            describe('job finished', () => {
                beforeEach(() => {
                    jobWaitingWorkflowResultsControllerFixture(moment(), 'successful');
                });

                it('should start elapsed timer', () => {
                    expect(workflowResultsService.createOneSecondTimer).not.toHaveBeenCalled();
                });
            });
        });

        describe('job transitions to running', () => {
            beforeEach(() => {
                jobWaitingWorkflowResultsControllerFixture(null, 'waiting');
                $rootScope.$broadcast('ws-jobs', { unified_job_id: workflow_job_json.id, status: "running" });
            });

            it('should start elapsed timer', () => {
                expect(scope.workflow.status).toBe("running");
                expect(workflowResultsService.createOneSecondTimer).toHaveBeenCalled();
            });
        });
    });
});
