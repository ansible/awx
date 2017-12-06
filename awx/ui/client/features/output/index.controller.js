import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

let ansi;
let $timeout;
let $sce;
let $compile;
let $scope;

const record = {};

const EVENT_START_TASK = 'playbook_on_task_start';
const EVENT_START_PLAY = 'playbook_on_play_start';
const EVENT_STATS_PLAY = 'playbook_on_stats';

const EVENT_GROUPS = [
    EVENT_START_TASK,
    EVENT_START_PLAY
];

const TIME_EVENTS = [
    EVENT_START_TASK,
    EVENT_START_PLAY,
    EVENT_STATS_PLAY
];

function JobsIndexController (job, _$sce_, _$timeout_, _$scope_, _$compile_) {
    $timeout = _$timeout_;
    $sce = _$sce_;
    $compile = _$compile_;
    $scope = _$scope_;
    ansi = new Ansi();

    const vm = this || {};
    const events = job.get('related.job_events.results');
    const html = $sce.trustAsHtml(parseEvents(events));

    vm.toggle = toggle;

    $timeout(() => {
        const table = $('#result-table');

        table.html($sce.getTrustedHtml(html));
        $compile(table.contents())($scope);
    });

    console.log(record);
}

function parseEvents (events) {
    events.sort(orderByLineNumber);

    return events.reduce((html, event) => `${html}${parseLine(event)}`, '');
}

function orderByLineNumber (a, b) {
    if (a.start_line > b.start_line) {
        return 1;
    }

    if (a.start_line < b.start_line) {
        return -1;
    }

    return 0;
}

function parseLine (event) {
    if (!event || !event.stdout) {
        return '';
    }

    const { stdout } = event;
    const lines = stdout.split('\r\n');

    let eventLine = event.start_line;
    let displayLine = event.start_line + 1;

    if (lines[0] === '') {
        displayLine++;
    }

    record[displayLine] = {
        line: displayLine,
        id: event.id,
        uuid: event.uuid,
        level: event.event_level,
        start: event.start_line,
        end: event.end_line,
        isTruncated: (event.end_line - event.start_line) > lines.length,
    };

    if (record[displayLine].isTruncated) {
        record[displayLine].truncatedAt = event.start_line + lines.length;
    }

    if (EVENT_GROUPS.includes(event.event)) {
        record[displayLine].isParent = true;
    }

    if (TIME_EVENTS.includes(event.event)) {
        record[displayLine].time = getTime(event.created);
    }

    const current = record[displayLine];

    return lines.reduce((html, line, i) => {
        eventLine++;

        const isLastLine = i === lines.length - 1;
        let append = createRow(eventLine, line, current);

        if (current.isTruncated && isLastLine) {
            append += createRow();
        }

        return `${html}${append}`;
    }, '');
}

function createRow (ln, content, current) {
    let expand = '';
    let timestamp = '';
    let toggleRow = '';
    let classList = '';

    content = content || '';

    if (hasAnsi(content)) {
        content = ansi.toHtml(content);
    }

    if (current) {
        if (current.line === ln) {
            if (current.isParent) {
                expand = '<i class="fa fa-chevron-down can-toggle"></i>';
                toggleRow = `<td class="at-Stdout-toggle" ng-click="vm.toggle(${ln})">${expand}</td>`;
            }

            if (current.time) {
                timestamp = current.time;
            }
        } else {
            classList += `child-of-${current.line}`;
        }
    }

    if (!toggleRow) {
        toggleRow = '<td class="at-Stdout-toggle"></td>';
    }

    if (!ln) {
        ln = '...';
    }

    return `
        <tr class="${classList}">
            ${toggleRow}
            <td class="at-Stdout-line">${ln}</td>
            <td class="at-Stdout-event">${content}</td>
            <td class="at-Stdout-time">${timestamp}</td>
        </tr>`;
}

function getTime (created) {
    const date = new Date(created);

    return `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
}

function toggle (line) {
    const lines = document.getElementsByClassName(`child-of-${line}`);
    console.log(lines);
}

JobsIndexController.$inject = ['job', '$sce', '$timeout', '$scope', '$compile'];

module.exports = JobsIndexController;
