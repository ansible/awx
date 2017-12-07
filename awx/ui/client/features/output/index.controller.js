import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

let vm;
let ansi;
let $timeout;
let $sce;
let $compile;
let $scope;

const record = {};
const meta = {};

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

    vm = this || {};
    const events = job.get('related.job_events.results');
    const html = $sce.trustAsHtml(parseEvents(events));

    vm.toggle = toggle;
    vm.menu = {
        expand: menuExpand,
        scrollToBottom: menuScrollToBottom,
        scrollToTop: menuScrollToTop
    };

    vm.state = {
        expand: true
    };

    $timeout(() => {
        const table = $('#result-table');

        table.html($sce.getTrustedHtml(html));
        $compile(table.contents())($scope);
    });
}

function menuExpand () {
    vm.state.expand = !vm.state.expand;
    vm.toggle(meta.parent);
}

function menuScrollToBottom () {
    const container = $('.at-Stdout-container')[0];

    container.scrollTo(0, container.scrollHeight);
}

function menuScrollToTop () {
    const container = $('.at-Stdout-container')[0];

    container.scrollTo(0, 0);
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
        info.parents = getParentEvents(event.parent_uuid);
    }

    if (info.isTruncated) {
        info.truncatedAt = event.start_line + lines.length;
    }

    if (EVENT_GROUPS.includes(event.event)) {
        info.isParent = true;

        if (event.event_level === 1) {
            meta.parent = event.uuid;
        }

        if (event.parent_uuid) {
            if (record[event.parent_uuid].children &&
                !record[event.parent_uuid].children.includes(event.uuid)) {
                record[event.parent_uuid].children.push(event.uuid);
            } else {
                record[event.parent_uuid].children = [event.uuid];
            }
        }
    }

    if (TIME_EVENTS.includes(event.event)) {
        info.time = getTime(event.created);
        info.line++;
    }

    record[event.uuid] = info;

    return info;
}

function getParentEvents (uuid, list) {
    list = list || [];

    if (record[uuid]) {
        list.push(uuid);
    }

    if (record[uuid].parents) {
        list = list.concat(record[uuid].parents);
    }

    return list;
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

        if (current.parents) {
            classList = current.parents.reduce((list, uuid) => `${list} child-of-${uuid}`, '');
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
    const lines = $(`.child-of-${uuid}`);
    let icon = $(`#${uuid} .at-Stdout-toggle > i`);

    if (record[uuid].children) {
        icon = icon.add($(`#${record[uuid].children.join(', #')}`).find('.at-Stdout-toggle > i'));
    }

    if (icon.hasClass('fa-chevron-down')) {
        icon.addClass('fa-chevron-right');
        icon.removeClass('fa-chevron-down');

        lines.addClass('hidden');
    } else {
        icon.addClass('fa-chevron-down');
        icon.removeClass('fa-chevron-right');

        lines.removeClass('hidden');
    }
}

JobsIndexController.$inject = ['job', '$sce', '$timeout', '$scope', '$compile'];

module.exports = JobsIndexController;
