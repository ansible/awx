'use strict';
import moment from 'moment';

describe('workflowResultsService', () => {
    let workflowResultsService;
    let $interval;

    beforeEach(angular.mock.module('workflowResults', ($provide) => {
        ['i18n', 'PromptDialog', 'Prompt', 'Wait', 'Rest', 'ProcessErrors', '$state', 'WorkflowJobModel', 'ComponentsStrings']
            .forEach(function(item) {
                $provide.value(item, {});
            });
        $provide.value('$stateExtender', { addState: jasmine.createSpy('addState'), });
        $provide.value('moment', moment);
    }));

    beforeEach(angular.mock.inject((_workflowResultsService_, _$interval_) => {
        workflowResultsService = _workflowResultsService_;
        $interval = _$interval_;
    }));

    describe('createOneSecondTimer()', () => {
        it('should create a timer that runs every second, incremented by a second', (done) => {
            let ticks = 0;
            let ticks_expected = 10;

            workflowResultsService.createOneSecondTimer(moment(), function() {
                ticks += 1;
                if (ticks >= ticks_expected) {
                    expect(ticks).toBe(ticks_expected);
                    // TODO: should verify time is 10 but this requires mocking moment()
                    // because we "artificially" accelerate time.
                    done();
                }
            });

            $interval.flush(ticks_expected * 1000);
        });
    });

    describe('destroyTimer()', () => {
        beforeEach(() => {
            $interval.cancel = jasmine.createSpy('cancel');
        });

        it('should not destroy null timer', () => {
            workflowResultsService.destroyTimer(null);

            expect($interval.cancel).not.toHaveBeenCalled();
        });

        it('should destroy passed in timer', () => {
            let timer = jasmine.createSpy('timer');

            workflowResultsService.destroyTimer(timer);

            expect($interval.cancel).toHaveBeenCalledWith(timer);
        });
    });
});
