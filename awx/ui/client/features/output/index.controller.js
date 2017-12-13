import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

let vm;
let ansi;
let jobEvent;
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

function JobsIndexController (job, JobEventModel, _$sce_, _$timeout_, _$scope_, _$compile_) {
    $timeout = _$timeout_;
    $sce = _$sce_;
    $compile = _$compile_;
    $scope = _$scope_;

    ansi = new Ansi();
    jobEvent = new JobEventModel();

    const events = job.get('related.job_events.results');
    const html = $sce.trustAsHtml(parseEvents(events));

    vm = this || {}; $scope.ns = 'jobs';
    $scope.jobs = {
        modal: {}
    };

    vm.toggle = toggle;
    vm.showHostDetails = showHostDetails;

    vm.menu = {
        top: {
            expand: menuExpand,
            isExpanded: false
        }
    };

    $timeout(() => {
        const table = $('#result-table');

        table.html($sce.getTrustedHtml(html));
        $compile(table.contents())($scope);
    });
}

function menuExpand () {
    vm.toggle(meta.parent);
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
        id: event.id,
        line: ln + 1,
        uuid: event.uuid,
        level: event.event_level,
        start: event.start_line,
        end: event.end_line,
        isTruncated: (event.end_line - event.start_line) > lines.length,
        isHost: typeof event.host === 'number'
    };

    if (info.isHost) {
        console.log(event);
    }

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
            if (record[event.parent_uuid]) {
                if (record[event.parent_uuid].children &&
                    !record[event.parent_uuid].children.includes(event.uuid)) {
                    record[event.parent_uuid].children.push(event.uuid);
                } else {
                    record[event.parent_uuid].children = [event.uuid];
                }
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

        if (record[uuid].parents) {
            list = list.concat(record[uuid].parents);
        }
    }

    return list;
}

function createRow (current, ln, content) {
    let id = '';
    let timestamp = '';
    let tdToggle = '';
    let tdEvent = '';
    let classList = '';

    content = content || '';

    if (hasAnsi(content)) {
        content = ansi.toHtml(content);
    }

    if (current) {
        if (current.isParent && current.line === ln) {
            id = current.uuid;
            tdToggle = `<td class="at-Stdout-toggle" ng-click="vm.toggle('${id}')"><i class="fa fa-chevron-down can-toggle"></i></td>`;
        }

        if (current.isHost) {
            tdEvent = `<td class="at-Stdout-event--host" ng-click="vm.showHostDetails('${current.id}')">${content}</td>`;
        }

        if (current.time && current.line === ln) {
            timestamp = current.time;
        }

        if (current.parents) {
            classList = current.parents.reduce((list, uuid) => `${list} child-of-${uuid}`, '');
        }
    }

    if (!tdEvent) {
        tdEvent = `<td class="at-Stdout-event">${content}</td>`;
    }

    if (!tdToggle) {
        tdToggle = '<td class="at-Stdout-toggle"></td>';
    }

    if (!ln) {
        ln = '...';
    }

    return `
        <tr id="${id}" class="${classList}">
            ${tdToggle}
            <td class="at-Stdout-line">${ln}</td>
            ${tdEvent}
            <td class="at-Stdout-time">${timestamp}</td>
        </tr>`;
}

function getTime (created) {
    const date = new Date(created);

    return `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
}

function showHostDetails (id) {
    jobEvent.request('get', id)
        .then(() => {
            const title = jobEvent.get('host_name');

            vm.host = {
                menu: true,
                stdout: jobEvent.get('stdout')
            };

            $scope.jobs.modal.show(title);
        });
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

JobsIndexController.$inject = ['job', 'JobEventModel', '$sce', '$timeout', '$scope', '$compile'];

module.exports = JobsIndexController;
