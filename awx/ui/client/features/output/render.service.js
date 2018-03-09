import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';
import Entities from 'html-entities';

const ELEMENT_TBODY = '#atStdoutResultTable';
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

const ansi = new Ansi();
const entities = new Entities.AllHtmlEntities();

function JobRenderService ($q, $sce, $window) {
    this.init = ({ compile, apply, get }) => {
        this.parent = null;
        this.record = {};
        this.el = $(ELEMENT_TBODY);
        this.hooks = { get, compile, apply };
    };

    this.sortByLineNumber = (a, b) => {
        if (a.start_line > b.start_line) {
            return 1;
        }

        if (a.start_line < b.start_line) {
            return -1;
        }

        return 0;
    };

    this.transformEventGroup = events => {
        let lines = 0;
        let html = '';

        events.sort(this.sortByLineNumber);

        events.forEach(event => {
            const line = this.transformEvent(event);

            html += line.html;
            lines += line.count;
        });

        return { html, lines };
    };

    this.transformEvent = event => {
        if (!event || !event.stdout) {
            return { html: '', count: 0 };
        }

        const stdout = this.sanitize(event.stdout);
        const lines = stdout.split('\r\n');

        let count = lines.length;
        let ln = event.start_line;

        const current = this.createRecord(ln, lines, event);

        const html = lines.reduce((concat, line, i) => {
            ln++;

            const isLastLine = i === lines.length - 1;

            let row = this.createRow(current, ln, line);

            if (current && current.isTruncated && isLastLine) {
                row += this.createRow(current);
                count++;
            }

            return `${concat}${row}`;
        }, '');

        return { html, count };
    };

    this.createRecord = (ln, lines, event) => {
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

        if (event.parent_uuid) {
            info.parents = this.getParentEvents(event.parent_uuid);
        }

        if (info.isTruncated) {
            info.truncatedAt = event.start_line + lines.length;
        }

        if (EVENT_GROUPS.includes(event.event)) {
            info.isParent = true;

            if (event.event_level === 1) {
                this.parent = event.uuid;
            }

            if (event.parent_uuid) {
                if (this.record[event.parent_uuid]) {
                    if (this.record[event.parent_uuid].children &&
                        !this.record[event.parent_uuid].children.includes(event.uuid)) {
                        this.record[event.parent_uuid].children.push(event.uuid);
                    } else {
                        this.record[event.parent_uuid].children = [event.uuid];
                    }
                }
            }
        }

        if (TIME_EVENTS.includes(event.event)) {
            info.time = this.getTimestamp(event.created);
            info.line++;
        }

        this.record[event.uuid] = info;

        return info;
    };

    this.createRow = (current, ln, content) => {
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
                tdToggle = `<td class="at-Stdout-toggle" ng-click="vm.toggle('${id}')"><i class="fa fa-angle-down can-toggle"></i></td>`;
            }

            if (current.isHost) {
                tdEvent = `<td class="at-Stdout-event--host" ng-click="vm.showHostDetails('${current.id}')">${content}</td>`;
            }

            if (current.time && current.line === ln) {
                timestamp = `<span>${current.time}</span>`;
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
    };

    this.getTimestamp = created => {
        const date = new Date(created);
        const hour = date.getHours() < 10 ? `0${date.getHours()}` : date.getHours();
        const minute = date.getMinutes() < 10 ? `0${date.getMinutes()}` : date.getMinutes();
        const second = date.getSeconds() < 10 ? `0${date.getSeconds()}` : date.getSeconds();

        return `${hour}:${minute}:${second}`;
    };

    this.getParentEvents = (uuid, list) => {
        list = list || [];

        if (this.record[uuid]) {
            list.push(uuid);

            if (this.record[uuid].parents) {
                list = list.concat(this.record[uuid].parents);
            }
        }

        return list;
    };

    this.getEvents = () => this.hooks.get();

    this.insert = (events, insert) => {
        const result = this.transformEventGroup(events);
        const html = this.trustHtml(result.html);

        return this.requestAnimationFrame(() => insert(html))
            .then(() => this.compile(html))
            .then(() => result.lines);
    };

    this.remove = elements => this.requestAnimationFrame(() => {
        elements.remove();
    });

    this.requestAnimationFrame = fn => $q(resolve => {
        $window.requestAnimationFrame(() => {
            if (fn) {
                fn();
            }

            return resolve();
        });
    });

    this.compile = html => {
        this.hooks.compile(html);

        return this.requestAnimationFrame();
    };

    this.clear = () => {
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

    this.prepend = events => this.insert(events, html => this.el.prepend(html));

    this.append = events => this.insert(events, html => this.el.append(html));

    this.trustHtml = html => $sce.getTrustedHtml($sce.trustAsHtml(html));

    this.sanitize = html => entities.encode(html);
}

JobRenderService.$inject = ['$q', '$sce', '$window'];

export default JobRenderService;
