import Ansi from 'ansi-to-html';
import Entities from 'html-entities';
import getUUID from 'uuid';

import {
    EVENT_START_PLAY,
    EVENT_STATS_PLAY,
    EVENT_START_TASK,
    OUTPUT_ELEMENT_TBODY,
    OUTPUT_EVENT_LIMIT,
} from './constants';

const EVENT_GROUPS = [
    EVENT_START_TASK,
    EVENT_START_PLAY,
];

const TIME_EVENTS = [
    EVENT_START_TASK,
    EVENT_START_PLAY,
    EVENT_STATS_PLAY,
];

const ansi = new Ansi();
const entities = new Entities.AllHtmlEntities();

// https://github.com/chalk/ansi-regex
const pattern = [
    '[\\u001B\\u009B][[\\]()#;?]*(?:(?:(?:[a-zA-Z\\d]*(?:;[a-zA-Z\\d]*)*)?\\u0007)',
    '(?:(?:\\d{1,4}(?:;\\d{0,4})*)?[\\dA-PRZcf-ntqry=><~]))'
].join('|');

const re = new RegExp(pattern);
const hasAnsi = input => re.test(input);

function JobRenderService ($q, $sce, $window) {
    this.init = ({ compile, toggles }) => {
        this.hooks = { compile };

        this.el = $(OUTPUT_ELEMENT_TBODY);
        this.parent = null;

        this.state = {
            head: null,
            tail: null,
            collapseAll: false,
            toggleMode: toggles,
        };

        this.counters = {};
        this.lines = {};
        this.records = {};
        this.uuids = {};

        this.missingCounterRecords = {};
        this.missingCounterUUIDs = {};
    };

    this.setCollapseAll = value => {
        this.state.collapseAll = value;
        Object.keys(this.records).forEach(key => {
            this.records[key].isCollapsed = value;
        });
    };

    this.sortByCounter = (a, b) => {
        if (a.counter > b.counter) {
            return 1;
        }

        if (a.counter < b.counter) {
            return -1;
        }

        return 0;
    };

    //
    // Event Data Transformation / HTML Building
    //

    this.appendEventGroup = events => {
        let lines = 0;
        let html = '';

        events.sort(this.sortByCounter);

        for (let i = 0; i <= events.length - 1; i++) {
            const current = events[i];
            const tailCounter = this.getTailCounter();

            if (tailCounter && (current.counter !== tailCounter + 1)) {
                const missing = this.appendMissingEventGroup(current);

                html += missing.html;
                lines += missing.count;
            }

            const line = this.transformEvent(current);

            html += line.html;
            lines += line.count;
        }

        return { html, lines };
    };

    this.appendMissingEventGroup = event => {
        const tailCounter = this.getTailCounter();
        const tail = this.lookupRecord(tailCounter);
        const tailMissing = this.isCounterMissing(tailCounter);

        if (!tailMissing && (!tail || !tail.counter)) {
            return { html: '', count: 0 };
        }

        let uuid;

        if (tailMissing) {
            uuid = this.missingCounterUUIDs[tailCounter];
        } else {
            uuid = getUUID();
        }

        const counters = [];

        for (let i = tailCounter + 1; i < event.counter; i++) {
            if (tailMissing) {
                this.missingCounterRecords[uuid].counters.push(i);
            } else {
                counters.push(i);
            }

            this.missingCounterUUIDs[i] = uuid;
        }

        if (tailMissing) {
            return { html: '', count: 0 };
        }

        const record = {
            counters,
            uuid,
            start: tail.end,
            end: event.start_line,
        };

        if (record.start === record.end) {
            return { html: '', count: 0 };
        }

        this.missingCounterRecords[uuid] = record;

        const html = `<div id="${uuid}" class="at-Stdout-row">
            <div class="at-Stdout-toggle"></div>
            <div class="at-Stdout-line-clickable" ng-click="vm.showMissingEvents('${uuid}')">...</div></div>`;
        const count = 1;

        return { html, count };
    };

    this.prependEventGroup = events => {
        let lines = 0;
        let html = '';

        events.sort(this.sortByCounter);

        for (let i = events.length - 1; i >= 0; i--) {
            const current = events[i];
            const headCounter = this.getHeadCounter();

            if (headCounter && (current.counter !== headCounter - 1)) {
                const missing = this.prependMissingEventGroup(current);

                html = missing.html + html;
                lines += missing.count;
            }

            const line = this.transformEvent(current);

            html = line.html + html;
            lines += line.count;
        }

        return { html, lines };
    };

    this.prependMissingEventGroup = event => {
        const headCounter = this.getHeadCounter();
        const head = this.lookupRecord(headCounter);
        const headMissing = this.isCounterMissing(headCounter);

        if (!headMissing && (!head || !head.counter)) {
            return { html: '', count: 0 };
        }

        let uuid;

        if (headMissing) {
            uuid = this.missingCounterUUIDs[headCounter];
        } else {
            uuid = getUUID();
        }

        const counters = [];

        for (let i = headCounter - 1; i > event.counter; i--) {
            if (headMissing) {
                this.missingCounterRecords[uuid].counters.unshift(i);
            } else {
                counters.unshift(i);
            }

            this.missingCounterUUIDs[i] = uuid;
        }

        if (headMissing) {
            return { html: '', count: 0 };
        }

        const record = {
            counters,
            uuid,
            start: event.end_line,
            end: head.start,
        };

        if (record.start === record.end) {
            return { html: '', count: 0 };
        }

        this.missingCounterRecords[uuid] = record;

        const html = `<div id="${uuid}" class="at-Stdout-row">
            <div class="at-Stdout-toggle"></div>
            <div class="at-Stdout-line-clickable" ng-click="vm.showMissingEvents('${uuid}')">...</div></div>`;
        const count = 1;

        return { html, count };
    };

    this.transformEvent = event => {
        if (event.uuid && this.records[event.uuid]) {
            return { html: '', count: 0 };
        }

        if (!event || !event.stdout) {
            return { html: '', count: 0 };
        }

        const stdout = this.sanitize(event.stdout);
        const lines = stdout.split('\r\n');
        const record = this.createRecord(event, lines);

        let html = '';
        let count = lines.length;
        let ln = event.start_line;

        for (let i = 0; i <= lines.length - 1; i++) {
            ln++;

            const line = lines[i];
            const isLastLine = i === lines.length - 1;

            let row = this.createRow(record, ln, line);

            if (record && record.isTruncated && isLastLine) {
                row += this.createRow(record);
                count++;
            }

            html += row;
        }

        return { html, count };
    };

    this.createRecord = (event, lines) => {
        if (!event.counter) {
            return null;
        }

        this.lines[event.counter] = event.end_line - event.start_line;

        if (this.state.tail === null ||
            this.state.tail < event.counter) {
            this.state.tail = event.counter;
        }

        if (this.state.head === null ||
            this.state.head > event.counter) {
            this.state.head = event.counter;
        }

        if (!event.uuid) {
            return null;
        }

        let isHost = false;
        if (typeof event.host === 'number') {
            isHost = true;
        } else if (event.type === 'project_update_event' &&
            event.event !== 'runner_on_skipped' &&
            event.event_data.host) {
            isHost = true;
        }

        const record = {
            isHost,
            id: event.id,
            line: event.start_line + 1,
            name: event.event,
            uuid: event.uuid,
            level: event.event_level,
            start: event.start_line,
            end: event.end_line,
            isTruncated: (event.end_line - event.start_line) > lines.length,
            lineCount: lines.length,
            isCollapsed: this.state.collapseAll,
            counter: event.counter,
        };

        if (event.parent_uuid) {
            record.parents = this.getParentEvents(event.parent_uuid);
            if (this.records[event.parent_uuid]) {
                record.isCollapsed = this.records[event.parent_uuid].isCollapsed;
            }
        }

        if (record.isTruncated) {
            record.truncatedAt = event.start_line + lines.length;
        }

        if (EVENT_GROUPS.includes(event.event)) {
            record.isParent = true;

            if (event.event_level === 1) {
                this.parent = event.uuid;
            }

            if (event.parent_uuid) {
                if (this.records[event.parent_uuid]) {
                    if (this.records[event.parent_uuid].children &&
                        !this.records[event.parent_uuid].children.includes(event.uuid)) {
                        this.records[event.parent_uuid].children.push(event.uuid);
                    } else {
                        this.records[event.parent_uuid].children = [event.uuid];
                    }
                }
            }
        }

        if (TIME_EVENTS.includes(event.event)) {
            record.time = this.getTimestamp(event.created);
            record.line++;
        }

        this.uuids[event.counter] = record.uuid;
        this.counters[event.uuid] = record.counter;
        this.records[event.uuid] = record;

        return record;
    };

    this.getParentEvents = (uuid, list) => {
        list = list || [];
        // always push its parent if exists
        list.push(uuid);
        // if we can get grandparent in current visible lines, we also push it
        if (this.records[uuid] && this.records[uuid].parents) {
            list = list.concat(this.records[uuid].parents);
        }

        return list;
    };

    this.deleteRecord = counter => {
        const uuid = this.uuids[counter];

        delete this.records[uuid];
        delete this.counters[uuid];
        delete this.uuids[counter];
        delete this.lines[counter];
    };

    this.getTimestamp = created => {
        const date = new Date(created);
        const hour = date.getHours() < 10 ? `0${date.getHours()}` : date.getHours();
        const minute = date.getMinutes() < 10 ? `0${date.getMinutes()}` : date.getMinutes();
        const second = date.getSeconds() < 10 ? `0${date.getSeconds()}` : date.getSeconds();

        return `${hour}:${minute}:${second}`;
    };

    this.createRow = (record, ln, content) => {
        let id = '';
        let icon = '';
        let timestamp = '';
        let tdToggle = '';
        let tdEvent = '';
        let classList = '';

        content = content || '';

        if (hasAnsi(content)) {
            content = ansi.toHtml(content);
        }

        if (record) {
            if (this.state.toggleMode && record.isParent && record.line === ln) {
                id = record.uuid;

                if (record.isCollapsed) {
                    icon = 'fa-angle-right';
                } else {
                    icon = 'fa-angle-down';
                }

                tdToggle = `<div class="at-Stdout-toggle" ng-click="vm.toggleCollapse('${id}')"><i class="fa ${icon} can-toggle"></i></div>`;
            }

            if (record.isHost) {
                tdEvent = `<div class="at-Stdout-event--host" ng-click="vm.showHostDetails('${record.id}', '${record.uuid}')"><span ng-non-bindable>${content}</span></div>`;
            }

            if (record.time && record.line === ln) {
                timestamp = `<span>${record.time}</span>`;
            }

            if (record.parents) {
                classList = record.parents.reduce((list, uuid) => `${list} child-of-${uuid}`, '');
            }
        }

        if (!tdEvent) {
            tdEvent = `<div class="at-Stdout-event"><span ng-non-bindable>${content}</span></div>`;
        }

        if (!tdToggle) {
            tdToggle = '<div class="at-Stdout-toggle"></div>';
        }

        if (!ln) {
            ln = '...';
        }

        if (record && record.isCollapsed) {
            if (record.level === 3 || record.level === 0) {
                classList += ' hidden';
            }
        }

        return `
            <div id="${id}" class="at-Stdout-row ${classList}">
                ${tdToggle}
                <div class="at-Stdout-line">${ln}</div>
                ${tdEvent}
                <div class="at-Stdout-time">${timestamp}</div>
            </div>`;
    };

    //
    // Element Operations
    //

    this.remove = elements => this.requestAnimationFrame(() => elements.remove());

    this.requestAnimationFrame = fn => $q(resolve => {
        $window.requestAnimationFrame(() => {
            if (fn) {
                fn();
            }

            return resolve();
        });
    });

    this.compile = content => {
        this.hooks.compile(content);

        return this.requestAnimationFrame();
    };

    this.removeAll = () => {
        const elements = this.el.children();
        return this.remove(elements);
    };

    this.shift = lines => {
        const elements = this.el.children().slice(0, lines);

        return this.remove(elements);
    };

    this.pop = lines => {
        const elements = this.el.children().slice(-lines);

        return this.remove(elements);
    };

    this.prepend = events => {
        if (events.length < 1) {
            return $q.resolve();
        }

        const result = this.prependEventGroup(events);
        const html = this.trustHtml(result.html);

        const newElements = angular.element(html);

        return this.requestAnimationFrame(() => this.el.prepend(newElements))
            .then(() => this.compile(newElements))
            .then(() => result.lines);
    };

    this.append = events => {
        if (events.length < 1) {
            return $q.resolve();
        }

        const result = this.appendEventGroup(events);
        const html = this.trustHtml(result.html);

        const newElements = angular.element(html);

        return this.requestAnimationFrame(() => this.el.append(newElements))
            .then(() => this.compile(newElements))
            .then(() => result.lines);
    };

    this.trustHtml = html => $sce.getTrustedHtml($sce.trustAsHtml(html));
    this.sanitize = html => entities.encode(html);

    //
    // Event Counter Methods - External code should use these.
    //

    this.getTailCounter = () => {
        if (this.state.tail === null) {
            return 0;
        }

        if (this.state.tail < 0) {
            return 0;
        }

        return this.state.tail;
    };

    this.getHeadCounter = () => {
        if (this.state.head === null) {
            return 0;
        }

        if (this.state.head < 0) {
            return 0;
        }

        return this.state.head;
    };

    this.getCapacity = () => OUTPUT_EVENT_LIMIT - Object.keys(this.lines).length;

    this.lookupRecord = counter => this.records[this.uuids[counter]];

    this.getLineCount = counter => {
        const record = this.lookupRecord(counter);

        if (record && record.lineCount) {
            return record.lineCount;
        }

        if (this.lines[counter]) {
            return this.lines[counter];
        }

        return 0;
    };

    this.deleteMissingCounterRecord = counter => {
        const uuid = this.missingCounterUUIDs[counter];

        delete this.missingCounterRecords[counter];
        delete this.missingCounterUUIDs[uuid];
    };

    this.clear = () => this.removeAll()
        .then(() => {
            const head = this.getHeadCounter();
            const tail = this.getTailCounter();

            for (let i = head; i <= tail; ++i) {
                this.deleteRecord(i);
                this.deleteMissingCounterRecord(i);
            }

            this.state.head = null;
            this.state.tail = null;

            return $q.resolve();
        });

    this.pushFront = events => {
        const tail = this.getTailCounter();

        return this.append(events.filter(({ counter }) => counter > tail));
    };

    this.pushBack = events => {
        const head = this.getHeadCounter();
        const tail = this.getTailCounter();

        return this.prepend(events.filter(({ counter }) => counter < head || counter > tail));
    };

    this.popMissing = counter => {
        const uuid = this.missingCounterUUIDs[counter];

        if (!this.missingCounterRecords[uuid]) {
            return 0;
        }

        this.missingCounterRecords[uuid].counters.pop();

        if (this.missingCounterRecords[uuid].counters.length > 0) {
            return 0;
        }

        delete this.missingCounterRecords[uuid];
        delete this.missingCounterUUIDs[counter];

        return 1;
    };

    this.shiftMissing = counter => {
        const uuid = this.missingCounterUUIDs[counter];

        if (!this.missingCounterRecords[uuid]) {
            return 0;
        }

        this.missingCounterRecords[uuid].counters.shift();

        if (this.missingCounterRecords[uuid].counters.length > 0) {
            return 0;
        }

        delete this.missingCounterRecords[uuid];
        delete this.missingCounterUUIDs[counter];

        return 1;
    };

    this.isCounterMissing = counter => this.missingCounterUUIDs[counter];

    this.popFront = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const max = this.getTailCounter();
        const min = max - count;

        let lines = 0;

        for (let i = max; i >= min; --i) {
            if (this.isCounterMissing(i)) {
                lines += this.popMissing(i);
            } else {
                lines += this.getLineCount(i);
            }
        }

        return this.pop(lines)
            .then(() => {
                for (let i = max; i >= min; --i) {
                    this.deleteRecord(i);
                    this.state.tail--;
                }

                return $q.resolve();
            });
    };

    this.popBack = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const min = this.getHeadCounter();
        const max = min + count;

        let lines = 0;

        for (let i = min; i <= max; ++i) {
            if (this.isCounterMissing(i)) {
                lines += this.popMissing(i);
            } else {
                lines += this.getLineCount(i);
            }
        }

        return this.shift(lines)
            .then(() => {
                for (let i = min; i <= max; ++i) {
                    this.deleteRecord(i);
                    this.state.head++;
                }

                return $q.resolve();
            });
    };
}

JobRenderService.$inject = ['$q', '$sce', '$window'];

export default JobRenderService;
