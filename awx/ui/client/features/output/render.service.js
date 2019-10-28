import Ansi from 'ansi-to-html';
import Entities from 'html-entities';

import {
    EVENT_START_PLAY,
    EVENT_STATS_PLAY,
    EVENT_START_TASK,
    OUTPUT_ANSI_COLORMAP,
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

const ansi = new Ansi({ stream: true, colors: OUTPUT_ANSI_COLORMAP });
const entities = new Entities.AllHtmlEntities();

// https://github.com/chalk/ansi-regex
const pattern = [
    '[\\u001B\\u009B][[\\]()#;?]*(?:(?:(?:[a-zA-Z\\d]*(?:;[a-zA-Z\\d]*)*)?\\u0007)',
    '(?:(?:\\d{1,4}(?:;\\d{0,4})*)?[\\dA-PRZcf-ntqry=><~]))'
].join('|');

const re = new RegExp(pattern);
const hasAnsi = input => re.test(input);

let $scope;

function JobRenderService ($q, $compile, $sce, $window) {
    this.init = (_$scope_, { toggles }) => {
        $scope = _$scope_;
        this.setScope();

        this.el = $(OUTPUT_ELEMENT_TBODY);
        this.parent = null;

        this.state = {
            head: 0,
            tail: 0,
            collapseAll: false,
            toggleMode: toggles,
        };

        this.records = {};
        this.uuids = {};
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

            if (this.state.tail && current.counter !== this.state.tail + 1) {
                const missing = this.appendMissingEventGroup(current);

                html += missing.html;
                lines += missing.count;
            }

            const eventLines = this.transformEvent(current);

            html += eventLines.html;
            lines += eventLines.count;
        }

        return { html, lines };
    };

    this.appendMissingEventGroup = event => {
        const tailUUID = this.uuids[this.state.tail];
        const tailRecord = this.records[tailUUID];

        if (!tailRecord) {
            return { html: '', count: 0 };
        }

        let uuid;

        if (tailRecord.isMissing) {
            uuid = tailUUID;
        } else {
            uuid = `${event.counter}-${tailUUID}`;
            this.records[uuid] = { uuid, counters: [], lineCount: 1, isMissing: true };
        }

        for (let i = this.state.tail + 1; i < event.counter; i++) {
            this.records[uuid].counters.push(i);
            this.uuids[i] = uuid;
        }

        if (tailRecord.isMissing) {
            return { html: '', count: 0 };
        }

        if (tailRecord.end === event.start_line) {
            return { html: '', count: 0 };
        }

        const html = this.buildRowHTML(this.records[uuid]);
        const count = 1;

        return { html, count };
    };

    this.prependEventGroup = events => {
        let lines = 0;
        let html = '';

        events.sort(this.sortByCounter);

        for (let i = events.length - 1; i >= 0; i--) {
            const current = events[i];

            if (this.state.head && current.counter !== this.state.head - 1) {
                const missing = this.prependMissingEventGroup(current);

                html = missing.html + html;
                lines += missing.count;
            }

            const eventLines = this.transformEvent(current);

            html = eventLines.html + html;
            lines += eventLines.count;
        }

        return { html, lines };
    };

    this.prependMissingEventGroup = event => {
        const headUUID = this.uuids[this.state.head];
        const headRecord = this.records[headUUID];

        if (!headRecord) {
            return { html: '', count: 0 };
        }

        let uuid;

        if (headRecord.isMissing) {
            uuid = headUUID;
        } else {
            uuid = `${headUUID}-${event.counter}`;
            this.records[uuid] = { uuid, counters: [], lineCount: 1, isMissing: true };
        }

        for (let i = this.state.head - 1; i > event.counter; i--) {
            this.records[uuid].counters.unshift(i);
            this.uuids[i] = uuid;
        }

        if (headRecord.isMissing) {
            return { html: '', count: 0 };
        }

        if (event.end_line === headRecord.start) {
            return { html: '', count: 0 };
        }

        const html = this.buildRowHTML(this.records[uuid]);
        const count = 1;

        return { html, count };
    };

    this.transformEvent = event => {
        if (!event || event.stdout === null || event.stdout === undefined) {
            return { html: '', count: 0 };
        }

        if (event.uuid && this.records[event.uuid] && !this.records[event.uuid]._isIncomplete) {
            return { html: '', count: 0 };
        }

        const stdout = this.sanitize(event.stdout);
        const lines = stdout.split('\r\n');
        const record = this.createRecord(event, lines);

        if (lines.length === 1 && lines[0] === '') {
            // runner_on_start, runner_on_ok, and a few other events have an actual line count
            // of 1 (stdout = '') and a claimed line count of 0 (end_line - start_line = 0).
            // Since a zero-length string has an actual line count of 1, they'll still get
            // rendered as blank lines unless we intercept them and add some special
            // handling to remove them.
            //
            // Although we're not going to render the blank line, the actual line count of
            // the zero-length stdout string, which is 1, has already been recorded at this
            // point so we must also go back and set the event's recorded line length to 0
            // in order to avoid deleting too many lines when we need to pop or shift a
            // page that contains this event off of the view.
            this.records[record.uuid].lineCount = 0;
            return { html: '', count: 0 };
        }

        let html = '';
        let count = lines.length;
        let ln = event.start_line;

        for (let i = 0; i <= lines.length - 1; i++) {
            ln++;

            const line = lines[i];
            const isLastLine = i === lines.length - 1;

            let row = this.buildRowHTML(record, ln, line);

            if (record && record.isTruncated && isLastLine) {
                row += this.buildRowHTML(record);
                count++;
            }

            html += row;
        }

        if (this.records[event.uuid]) {
            this.records[event.uuid].lineCount = count;
        }

        return { html, count };
    };

    this.createRecord = (event, lines) => {
        if (!event.counter) {
            return null;
        }

        if (!this.state.head || event.counter < this.state.head) {
            this.state.head = event.counter;
        }

        if (!this.state.tail || event.counter > this.state.tail) {
            this.state.tail = event.counter;
        }

        if (!event.uuid) {
            this.uuids[event.counter] = event.counter;
            this.records[event.counter] = { counters: [event.counter], lineCount: lines.length };

            return this.records[event.counter];
        }

        let isClickable = false;
        if (typeof event.host === 'number' || event.event_data && event.event_data.res) {
            isClickable = true;
        } else if (event.type === 'project_update_event' &&
            event.event !== 'runner_on_skipped' &&
            event.event_data.host) {
            isClickable = true;
        }

        const children = (this.records[event.uuid] && this.records[event.uuid].children)
            ? this.records[event.uuid].children : [];

        const record = {
            isClickable,
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
            counters: [event.counter],
            children
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
                    if (this.records[event.parent_uuid].children) {
                        if (!this.records[event.parent_uuid].children.includes(event.uuid)) {
                            this.records[event.parent_uuid].children.push(event.uuid);
                        }
                    } else {
                        this.records[event.parent_uuid].children = [event.uuid];
                    }
                } else {
                    this.records[event.parent_uuid] = {
                        _isIncomplete: true,
                        children: [event.uuid]
                    };
                }
            }
        }

        if (TIME_EVENTS.includes(event.event)) {
            record.time = this.getTimestamp(event.created);
            record.line++;
        }

        this.records[event.uuid] = record;
        this.uuids[event.counter] = event.uuid;

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

    this.buildRowHTML = (record, ln, content) => {
        let id = '';
        let icon = '';
        let timestamp = '';
        let tdToggle = '';
        let tdEvent = '';
        let classList = '';
        let directives = '';

        if (record.isMissing) {
            return `<div id="${record.uuid}" class="at-Stdout-row">
                <div class="at-Stdout-toggle"></div>
                <div class="at-Stdout-line at-Stdout-line--clickable" ng-click="vm.showMissingEvents('${record.uuid}')">...</div></div>`;
        }

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
                classList += ' at-Stdout-row--hidden';
            }
        }

        if (record && record.isClickable) {
            classList += ' at-Stdout-row--clickable';
            directives = `ng-click="vm.showHostDetails('${record.id}', '${record.uuid}')"`;
        }

        return `
            <div id="${id}" class="at-Stdout-row ${classList}" ${directives}>
                ${tdToggle}
                <div class="at-Stdout-line">${ln}</div>
                <div class="at-Stdout-event"><span ng-non-bindable>${content}</span></div>
                <div class="at-Stdout-time">${timestamp}</div>
            </div>
        `;
    };

    this.getTimestamp = created => {
        const date = new Date(created);
        const hour = date.getHours() < 10 ? `0${date.getHours()}` : date.getHours();
        const minute = date.getMinutes() < 10 ? `0${date.getMinutes()}` : date.getMinutes();
        const second = date.getSeconds() < 10 ? `0${date.getSeconds()}` : date.getSeconds();

        return `${hour}:${minute}:${second}`;
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

    this.setScope = () => {
        if (this.scope) this.scope.$destroy();
        delete this.scope;

        this.scope = $scope.$new();
    };

    this.compile = () => {
        this.setScope();
        $compile(this.el)(this.scope);

        return this.requestAnimationFrame();
    };

    this.removeAll = () => {
        const elements = this.el.contents();
        return this.remove(elements);
    };

    this.shift = lines => {
        // We multiply by two here under the assumption that one element and one text node
        // is generated for each line of output.
        const count = (2 * lines) + 1;
        const elements = this.el.contents().slice(0, count);

        return this.remove(elements);
    };

    this.pop = lines => {
        // We multiply by two here under the assumption that one element and one text node
        // is generated for each line of output.
        const count = (2 * lines) + 1;
        const elements = this.el.contents().slice(-count);

        return this.remove(elements);
    };

    this.prepend = events => {
        if (events.length < 1) {
            return $q.resolve();
        }

        const result = this.prependEventGroup(events);
        const html = this.trustHtml(result.html);

        return this.requestAnimationFrame(() => this.el.prepend(html))
            .then(() => result.lines);
    };

    this.append = events => {
        if (events.length < 1) {
            return $q.resolve();
        }

        const result = this.appendEventGroup(events);
        const html = this.trustHtml(result.html);

        return this.requestAnimationFrame(() => this.el.append(html))
            .then(() => result.lines);
    };

    this.trustHtml = html => $sce.getTrustedHtml($sce.trustAsHtml(html));
    this.sanitize = html => entities.encode(html);

    //
    // Event Counter Methods - External code should prefer these.
    //

    this.clear = () => this.removeAll()
        .then(() => {
            const head = this.getHeadCounter();
            const tail = this.getTailCounter();

            for (let i = head; i <= tail; ++i) {
                const uuid = this.uuids[i];

                if (uuid) {
                    delete this.records[uuid];
                    delete this.uuids[i];
                }
            }

            this.state.head = 0;
            this.state.tail = 0;

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

    this.popFront = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const max = this.state.tail;
        const min = max - count + 1;

        let lines = 0;

        for (let i = max; i >= min; --i) {
            const uuid = this.uuids[i];

            if (!uuid) {
                continue;
            }

            this.records[uuid].counters.pop();
            delete this.uuids[i];

            if (this.records[uuid].counters.length === 0) {
                lines += this.records[uuid].lineCount;

                delete this.records[uuid];
                this.state.tail--;
            }
        }

        return this.pop(lines);
    };

    this.popBack = count => {
        if (!count || count <= 0) {
            return $q.resolve();
        }

        const min = this.state.head;
        const max = min + count - 1;

        let lines = 0;

        for (let i = min; i <= max; ++i) {
            const uuid = this.uuids[i];

            if (!uuid) {
                continue;
            }

            this.records[uuid].counters.shift();
            delete this.uuids[i];

            if (this.records[uuid].counters.length === 0) {
                lines += this.records[uuid].lineCount;

                delete this.records[uuid];
                this.state.head++;
            }
        }

        return this.shift(lines);
    };

    this.getHeadCounter = () => this.state.head;
    this.getTailCounter = () => this.state.tail;
    this.getCapacity = () => OUTPUT_EVENT_LIMIT - (this.getTailCounter() - this.getHeadCounter());
}

JobRenderService.$inject = ['$q', '$compile', '$sce', '$window'];

export default JobRenderService;
