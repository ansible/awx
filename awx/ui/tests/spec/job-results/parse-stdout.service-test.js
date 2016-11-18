'use strict';

describe('parseStdoutService', () => {
    let parseStdoutService,
        log;

    beforeEach(angular.mock.module('Tower'));

    beforeEach(angular.mock.module('jobResults',($provide) => {
        log = jasmine.createSpyObj('$log', [
            'error'
        ]);

        $provide.value('$log', log);
    }));

    beforeEach(angular.mock.inject((_$log_, _parseStdoutService_) => {
        parseStdoutService = _parseStdoutService_;
    }));

    describe('prettify()', () => {
        it('returns lines of stdout with styling classes', () => {
            let line = "[0;32mok: [host-00][0m",
            styledLine = '<span class="ansi32">ok: [host-00]</span>';
            expect(parseStdoutService.prettify(line).toBe(styledLine));
        });

        it('can return lines of stdout without styling classes', () => {
            let line = "[0;32mok: [host-00][0m",
            unstyled = "unstyled",
            unstyledLine = 'ok: [host-00]';
            expect(parseStdoutService.prettify(line, unstyled).toBe(unstyledLine));
        });
    });

    describe('getLineClasses()', () => {
        it('creates a string that is used as a class', () => {
            let headerEvent = {
                event_name: 'playbook_on_task_start',
                event_data: {
                    task_uuid: '1da9012d-18e6-4562-85cd-83cf10a97f86'
                }
            };
            let lineNum = 3;
            let line = "TASK [setup] *******************************************************************";
            let styledLine =  "header_task header_task_80dd087c-268b-45e8-9aab-1083bcfd9364 play_0f667a23-d9ab-4128-a735-80566bcdbca0 line_num_3";
            expect(parseStdoutService.getLineClasses(headerEvent, line, lineNum).toBe(styledLine));
        });


    });

    describe('getCollapseIcon()', () => {
        let emptySpan = `
<span class="JobResultsStdOut-lineExpander"></span>`;

        it('returns empty expander for non-header event', () => {
            let nonHeaderEvent = {
                event_name: 'not_header',
                start_line: 0,
                end_line: 1,
                stdout:"line1"
            };
            expect(parseStdoutService.getCollapseIcon(nonHeaderEvent))
                .toBe(emptySpan);
        });

        it('returns collapse/decollapse icons for header events', () => {
            let headerEvent = {
                event_name: 'playbook_on_task_start',
                start_line: 0,
                end_line: 1,
                stdout:"line1",
                event_data: {
                    task_uuid: '1da9012d-18e6-4562-85cd-83cf10a97f86'
                }
            };
            let line = "TASK [setup] *******************************************************************";
            let expandSpan = `
<span class="JobResultsStdOut-lineExpander">
<i class="JobResultsStdOut-lineExpanderIcon fa fa-caret-down expanderizer
    expanderizer--task expanded"
    ng-click="toggleLine($event, '.task_1da9012d-18e6-4562-85cd-83cf10a97f86')"
    data-uuid="task_1da9012d-18e6-4562-85cd-83cf10a97f86">
</i>
</span>`;
            expect(parseStdoutService.getCollapseIcon(headerEvent, line))
                .toBe(expandSpan);
        });
    });

    describe('getLineArr()', () => {
        it('returns stdout in array format', () => {
            let mockEvent = {
                start_line: 12,
                end_line: 14,
                stdout: "line1\r\nline2\r\n"
            };
            let expectedReturn = [[13, "line1"],[14, "line2"]];

            let returnedEvent = parseStdoutService.getLineArr(mockEvent);

            expect(returnedEvent).toEqual(expectedReturn);
        });
    });

    describe('parseStdout()', () => {
        let mockEvent = {"foo": "bar"};

        it('calls functions', function() {
            spyOn(parseStdoutService, 'getLineArr').and
                .returnValue([[13, 'line1'], [14, 'line2']]);
            spyOn(parseStdoutService, 'getLineClasses').and
                .returnValue("");
            spyOn(parseStdoutService, 'getCollapseIcon').and
                .returnValue("");
            spyOn(parseStdoutService, 'getAnchorTags').and
                .returnValue("");
            spyOn(parseStdoutService, 'prettify').and
                .returnValue("prettified_line");

            parseStdoutService.parseStdout(mockEvent);

            expect(parseStdoutService.getLineArr)
                .toHaveBeenCalledWith(mockEvent);
            expect(parseStdoutService.getLineClasses)
                .toHaveBeenCalledWith(mockEvent, 'line1', 13);
            expect(parseStdoutService.getCollapseIcon)
                .toHaveBeenCalledWith(mockEvent, 'line1');
            expect(parseStdoutService.getAnchorTags)
                .toHaveBeenCalledWith(mockEvent, "prettified_line");
            expect(parseStdoutService.prettify)
                .toHaveBeenCalledWith('line1');

            // get line arr should be called once for the event
            expect(parseStdoutService.getLineArr.calls.count())
                .toBe(1);

            // other functions should be called twice (once for each
            // line)
            expect(parseStdoutService.getLineClasses.calls.count())
                .toBe(2);
            expect(parseStdoutService.getCollapseIcon.calls.count())
                .toBe(2);
            expect(parseStdoutService.getAnchorTags.calls.count())
                .toBe(2);
            expect(parseStdoutService.prettify.calls.count())
                .toBe(2);
        });

        it('returns dom-ified lines', function() {
            spyOn(parseStdoutService, 'getLineArr').and
                .returnValue([[13, 'line1']]);
            spyOn(parseStdoutService, 'getLineClasses').and
                .returnValue("line_classes");
            spyOn(parseStdoutService, 'getCollapseIcon').and
                .returnValue("collapse_icon_dom");
            spyOn(parseStdoutService, 'getAnchorTags').and
                .returnValue("anchor_tag_dom");
            spyOn(parseStdoutService, 'prettify').and
                .returnValue("prettified_line");

            var returnedString = parseStdoutService.parseStdout(mockEvent);

            var expectedString = `
<div class="JobResultsStdOut-aLineOfStdOutline_classes">
    <div class="JobResultsStdOut-lineNumberColumn">collapse_icon_dom13</div>
    <div class="JobResultsStdOut-stdoutColumn">anchor_tag_dom</div>
</div>`;
            expect(returnedString).toBe(expectedString);
        });
    });
});
