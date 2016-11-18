'use strict';

describe('', () => {
    let parseStdoutService,
        $log;

    beforeEach(angular.mock.module('Tower'));

    beforeEach(angular.mock.module('jobResults', function($provide){
        // $log = jasmine.createSpyObj('$log', [
        //     'error'
        // ]);
        // $provide.value('$log', $log);
    }));

    beforeEach(angular.mock.inject((_$log_, _parseStdoutService_) => {
        parseStdoutService = _parseStdoutService_;
    }));

    describe('parseStdout()', () => {
        it('returns the line number and text from an event object', () => {
            var service = parseStdoutService,
            span = '<span class="JobResultsStdOut-lineExpander"></span>`',
            event = {
                start_line: 0,
                end_line: 1,
                stdout:"PLAY [all] *********************************************************************"
            };

            expect(parseStdoutService.parseStdout(event)).toBe(span);
        })
    });
});
