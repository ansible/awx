import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';

let vm;
let ansi;
let model;
let resource;
let page;
let container;
let $timeout;
let $sce;
let $compile;
let $scope;
let $q;

const record = {};

let parent = null;

const SCROLL_THRESHOLD = 0.1;
const SCROLL_DELAY = 1000;
const EVENT_START_TASK = 'playbook_on_task_start';
const EVENT_START_PLAY = 'playbook_on_play_start';
const EVENT_STATS_PLAY = 'playbook_on_stats';
const ELEMENT_TBODY = '#atStdoutResultTable';
const ELEMENT_CONTAINER = '.at-Stdout-container';
const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';

const EVENT_GROUPS = [
    EVENT_START_TASK,
    EVENT_START_PLAY
];

const TIME_EVENTS = [
    EVENT_START_TASK,
    EVENT_START_PLAY,
    EVENT_STATS_PLAY
];

function JobsIndexController (
    _resource_,
    _page_,
    _$sce_,
    _$timeout_,
    _$scope_,
    _$compile_,
    _$q_
) {
    vm = this || {};

    $timeout = _$timeout_;
    $sce = _$sce_;
    $compile = _$compile_;
    $scope = _$scope_;
    $q = _$q_;
    resource = _resource_;
    page = _page_;
    model = resource.model;

    ansi = new Ansi();

    const events = model.get(`related.${resource.related}.results`);
    const parsed = parseEvents(events);
    const html = $sce.trustAsHtml(parsed.html);

    page.init(resource);

    page.add({ number: 1, lines: parsed.lines });

    // Development helper(s)
    vm.clear = devClear;

    // Stdout Navigation
    vm.scroll = {
        isLocked: false,
        showBackToTop: false,
        isActive: false,
        position: 0,
        time: 0,
        home: scrollHome,
        end: scrollEnd,
        down: scrollPageDown,
        up: scrollPageUp
    };

    // Expand/collapse
    vm.toggle = toggle;
    vm.expand = expand;
    vm.isExpanded = true;

    // Real-time (active between JOB_START and JOB_END events only)
    $scope.$on(resource.ws.namespace, processWebSocketEvents);
    vm.stream = {
        isActive: false,
        isRendering: false,
        isPaused: false,
        buffered: 0,
        count: 0,
        page: 1
    };

    window.requestAnimationFrame(() => {
        const table = $(ELEMENT_TBODY);
        container = $(ELEMENT_CONTAINER);

        table.html($sce.getTrustedHtml(html));
        $compile(table.contents())($scope);

        container.scroll(onScroll);
    });
}

function processWebSocketEvents (scope, data) {
    let done;

    if (data.event === JOB_START) {
        vm.scroll.isActive = true;
        vm.stream.isActive = true;
        vm.scroll.isLocked = true;
    } else if (data.event === JOB_END) {
        vm.stream.isActive = false;
    }

    const pageAdded = page.addToBuffer(data);

    if (pageAdded && !vm.scroll.isLocked) {
        vm.stream.isPaused = true;
    }

    if (vm.stream.isPaused && vm.scroll.isLocked) {
        vm.stream.isPaused = false;
    }

    if (vm.stream.isRendering || vm.stream.isPaused) {
        return;
    }

    const events = page.emptyBuffer();

    return render(events);
}

function render (events) {
    vm.stream.isRendering = true;

    return shift()
        .then(() => append(events))
        .then(() => {
            if (vm.scroll.isLocked) {
                const height = container[0].scrollHeight;
                container[0].scrollTop = height;
            }

            if (!vm.stream.isActive) {
                const buffer = page.emptyBuffer();

                if (buffer.length) {
                    return render(buffer);
                }

                vm.stream.isRendering = false;
                vm.scroll.isLocked = false;
                vm.scroll.isActive = false;
            } else {
                vm.stream.isRendering = false;
            }
        });
}

function devClear () {
    page.init(resource);
    clear();
}

function next () {
    return page.next()
        .then(events => {
            if (!events) {
                return;
            }

            return shift()
                .then(() => append(events));
        })
}

function previous () {
    const container = $(ELEMENT_CONTAINER)[0];

    let previousHeight;

    return page.previous()
        .then(events => {
            if (!events) {
                return;
            }

            return pop()
                .then(() => {
                    previousHeight = container.scrollHeight;

                    return prepend(events);
                })
                .then(()  => {
                    const currentHeight = container.scrollHeight;
                    container.scrollTop = currentHeight - previousHeight;
                });
        });
}

function append (events) {
    return $q(resolve => {
        window.requestAnimationFrame(() => {
            const parsed = parseEvents(events);
            const rows = $($sce.getTrustedHtml($sce.trustAsHtml(parsed.html)));
            const table = $(ELEMENT_TBODY);

            page.updateLineCount('current', parsed.lines);

            table.append(rows);
            $compile(rows.contents())($scope);

            return resolve();
        });
    });
}

function prepend (events) {
    return $q(resolve => {
        window.requestAnimationFrame(() => {
            const parsed = parseEvents(events);
            const rows = $($sce.getTrustedHtml($sce.trustAsHtml(parsed.html)));
            const table = $(ELEMENT_TBODY);

            page.updateLineCount('current', parsed.lines);

            table.prepend(rows);
            $compile(rows.contents())($scope);

            $scope.$apply(() => {
                return resolve(parsed.lines);
            });
        });
    });
}

function pop () {
    return $q(resolve => {
        if (!page.isOverCapacity()) {
            return resolve();
        }

        window.requestAnimationFrame(() => {
            const lines = page.trim('right');
            const rows = $(ELEMENT_TBODY).children().slice(-lines);

            rows.empty();
            rows.remove();

            return resolve();
        });
    });
}

function shift () {
    return $q(resolve => {
        if (!page.isOverCapacity()) {
            return resolve();
        }

        window.requestAnimationFrame(() => {
            const lines = page.trim('left');
            const rows = $(ELEMENT_TBODY).children().slice(0, lines);

            rows.empty();
            rows.remove();

            return resolve();
        });
    });
}

function clear () {
    return $q(resolve => {
        window.requestAnimationFrame(() => {
            const rows = $(ELEMENT_TBODY).children();

            rows.empty();
            rows.remove();

            return resolve();
        });
    });
}

function expand () {
    vm.toggle(parent, true);
}

function parseEvents (events) {
    let lines = 0;
    let html = '';

    events.sort(orderByLineNumber);

    events.forEach(event => {
        const line = parseLine(event);

        html += line.html;
        lines += line.count;
    });

    return {
        html,
        lines
    };
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
        return { html: '', count: 0 };
    }

    const { stdout } = event;
    const lines = stdout.split('\r\n');

    let count = lines.length;
    let ln = event.start_line;

    const current = createRecord(ln, lines, event);

    const html = lines.reduce((html, line, i) => {
        ln++;

        const isLastLine = i === lines.length - 1;
        let row = createRow(current, ln, line);

        if (current && current.isTruncated && isLastLine) {
            row += createRow(current);
            count++;
        }

        return `${html}${row}`;
    }, '');

    return { html, count };
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

    if (event.parent_uuid) {
        info.parents = getParentEvents(event.parent_uuid);
    }

    if (info.isTruncated) {
        info.truncatedAt = event.start_line + lines.length;
    }

    if (EVENT_GROUPS.includes(event.event)) {
        info.isParent = true;

        if (event.event_level === 1) {
            parent = event.uuid;
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
}

function getTime (created) {
    const date = new Date(created);
    const hour = date.getHours() < 10 ? `0${date.getHours()}` : date.getHours();
    const minute = date.getMinutes() < 10 ? `0${date.getMinutes()}` : date.getMinutes();
    const second = date.getSeconds() < 10 ? `0${date.getSeconds()}` : date.getSeconds();

    return `${hour}:${minute}:${second}`;
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

function toggle (uuid, menu) {
    const lines = $(`.child-of-${uuid}`);
    let icon = $(`#${uuid} .at-Stdout-toggle > i`);

    if (menu || record[uuid].level === 1) {
        vm.isExpanded = !vm.isExpanded;
    }

    if (record[uuid].children) {
        icon = icon.add($(`#${record[uuid].children.join(', #')}`).find('.at-Stdout-toggle > i'));
    }

    if (icon.hasClass('fa-angle-down')) {
        icon.addClass('fa-angle-right');
        icon.removeClass('fa-angle-down');

        lines.addClass('hidden');
    } else {
        icon.addClass('fa-angle-down');
        icon.removeClass('fa-angle-right');

        lines.removeClass('hidden');
    }
}

function onScroll () {
    if (vm.scroll.isActive) {
        return;
    }

    if (vm.scroll.register) {
        $timeout.cancel(vm.scroll.register);
    }

    vm.scroll.register = $timeout(registerScrollEvent, SCROLL_DELAY);
}

function registerScrollEvent () {
    vm.scroll.isActive = true;

    const position = container[0].scrollTop;
    const height = container[0].offsetHeight;
    const downward = position > vm.scroll.position;

    let promise;

    if (position !== 0 ) {
        vm.scroll.showBackToTop = true;
    } else {
        vm.scroll.showBackToTop = false;
    }


    console.log('downward', downward);
    if (downward) {
        if (((height - position) / height) < SCROLL_THRESHOLD) {
            promise = next;
        }
    } else {
        if ((position / height) < SCROLL_THRESHOLD) {
            console.log('previous');
            promise = previous;
        }
    }

    vm.scroll.position = position;

    if (!promise) {
        vm.scroll.isActive = false;

        return $q.resolve();
    }

    return promise()
        .then(() => {
            console.log('done');
            vm.scroll.isActive = false;
            /*
             *$timeout(() => {
             *    vm.scroll.isActive = false;
             *}, SCROLL_DELAY);
             */
        });

}

function scrollHome () {
    return page.first()
        .then(events => {
            if (!events) {
                return;
            }

            return clear()
                .then(() => prepend(events))
                .then(() => {
                    vm.scroll.isActive = false;
                });
        });
}

function scrollEnd () {
    if (vm.scroll.isLocked) {
        page.bookmark();

        vm.scroll.isLocked = false;
        vm.scroll.isActive = false;

        return;
    } else if (!vm.scroll.isLocked && vm.stream.isActive) {
        page.bookmark();

        vm.scroll.isActive = true;
        vm.scroll.isLocked = true;

        return;
    }

    vm.scroll.isActive = true;

    return page.last()
        .then(events => {
            if (!events) {
                return;
            }

            return clear()
                .then(() => append(events))
                .then(() => {
                    const container = $(ELEMENT_CONTAINER)[0];

                    container.scrollTop = container.scrollHeight;
                    vm.scroll.isActive = false;
                });
        });
}

function scrollPageUp () {
    const container = $(ELEMENT_CONTAINER)[0];
    const jump = container.scrollTop - container.offsetHeight;

    container.scrollTop = jump;
}

function scrollPageDown () {
    const container = $(ELEMENT_CONTAINER)[0];
    const jump = container.scrollTop + container.offsetHeight;

    container.scrollTop = jump;
}

JobsIndexController.$inject = [
    'resource',
    'JobPageService',
    '$sce',
    '$timeout',
    '$scope',
    '$compile',
    '$q'
];

module.exports = JobsIndexController;
