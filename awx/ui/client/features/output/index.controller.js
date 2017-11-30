import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

let ansi;

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

function JobsIndexController (job, $sce) {
    const vm = this || {};
    const events = job.get('related.job_events.results');

    ansi = new Ansi();

    const html = parseEvents(events);

    vm.html = $sce.trustAsHtml(html);
    vm.toggle = toggle;
}

function parseEvents (events) {
    events.sort(orderByLineNumber);

    console.log(events);
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
    const isTruncated = (event.end_line - event.start_line) > lines.length;

    let ln = event.start_line;

    return lines.reduce((html, line, i) => {
        ln++;

        const time = getTime(event, i);
        const group = getGroup(event, i);
        const isLastLine = i === lines.length - 1;

        if (isTruncated && isLastLine) {
            return `${html}${createRow(ln, line, time, group)}${createTruncatedRow(event.id)}`;
        }

        return `${html}${createRow(ln, line, time, group)}`;
    }, '');
}

function createTruncatedRow (id) {
    return `
        <tr class="${id}">
            <td class="at-Stdout-toggle"></td>
            <td class="at-Stdout-line text-center">...</td>
            <td class="at-Stdout-event"></td>
            <td class="at-Stdout-time"></td>
        </tr>`;
}

function createRow (ln, content, time, group) {
    content = hasAnsi(content) ? ansi.toHtml(content) : content;

    let expand = '';
    if (group.parent) {
        expand = '<i class="fa fa-chevron-down" ng-click="vm.toggle(group.level)"></i>';
    }

    return `
        <tr class="${group.classList}">
            <td class="at-Stdout-toggle">${expand}</td>
            <td class="at-Stdout-line">${ln}</td>
            <td class="at-Stdout-event">${content}</td>
            <td class="at-Stdout-time">${time}</td>
        </tr>`;
}

function getGroup (event, i) {
    const group = {};

    if (EVENT_GROUPS.includes(event.event) && i === 1) {
        group.parent = true;
        group.classList = `parent parent-${event.event_level}`;
    } else {
        group.classList = '';
    }

    group.level = event.event_level;

    return group;
}

function getTime (event, i) {
    if (!TIME_EVENTS.includes(event.event) || i !== 1) {
        return '';
    }

    const date = new Date(event.created);

    return `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
}

function toggle (id) {
    console.log(id);
}
/*
 *
 *function getTruncatedEvent () {
 *
 *}
 *
 *function addDynamic (start) {
 *    document.getElementsByClassName('parent')
 *}
 *
 */
JobsIndexController.$inject = ['job', '$sce'];

module.exports = JobsIndexController;
