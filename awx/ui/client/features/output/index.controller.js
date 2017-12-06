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

    let ln = event.start_line;

    const current = createRecord(ln, lines, event);

    return lines.reduce((html, line, i) => {
        ln++;

        const isLastLine = i === lines.length - 1;
        let append = createRow(current, ln, line);

        if (current && current.isTruncated && isLastLine) {
            append += createRow(current);
        }

        return `${html}${append}`;
    }, '');
}

function createRecord (ln, lines, event) {
    if (!event.uuid) {
        return null;
    }

    const info = {
        line: ln + 1,
        uuid: event.uuid,
        level: event.event_level,
        start: event.start_line,
        end: event.end_line,
        isTruncated: (event.end_line - event.start_line) > lines.length
    };

    if (event.parent_uuid) {
        info.childOf = event.parent_uuid;
    }

    if (info.isTruncated) {
        info.truncatedAt = event.start_line + lines.length;
    }

    if (EVENT_GROUPS.includes(event.event)) {
        info.isParent = true;
    }

    if (TIME_EVENTS.includes(event.event)) {
        info.time = getTime(event.created);
        info.line++;
    }

    record[event.uuid] = info;

    return info;
}

function createRow (current, ln, content) {
    let expand = '';
    let timestamp = '';
    let toggleRow = '';
    let classList = '';
    let id = '';

    content = content || '';

    if (hasAnsi(content)) {
        content = ansi.toHtml(content);
    }

    if (current) {
        if (current.isParent && current.line === ln) {
            id = current.uuid;
            expand = '<i class="fa fa-chevron-down can-toggle"></i>';
            toggleRow = `<td class="at-Stdout-toggle" ng-click="vm.toggle('${current.uuid}')">${expand}</td>`;
        }

        if (current.time && current.line === ln) {
            timestamp = current.time;
        }

        if (!classList) {
            classList += `child-of-${current.childOf}`;
        }
    }

    if (!toggleRow) {
        toggleRow = '<td class="at-Stdout-toggle"></td>';
    }

    if (!ln) {
        ln = '...';
    }

    return `
        <tr id="${id}" class="${classList}">
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

function toggle (uuid) {
    const i = $(`#${uuid} .at-Stdout-toggle > i`);

    if (i.hasClass('fa-chevron-down')) {
        i.addClass('fa-chevron-right');
        i.removeClass('fa-chevron-down');

        $(`.child-of-${uuid}`).addClass('hidden');
    } else {
        i.addClass('fa-chevron-down');
        i.removeClass('fa-chevron-right');

        $(`.child-of-${uuid}`).removeClass('hidden');
    }
}

JobsIndexController.$inject = ['job', '$sce', '$timeout', '$scope', '$compile'];

module.exports = JobsIndexController;
