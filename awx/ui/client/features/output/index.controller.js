const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';

let vm;
let $compile;
let $scope;
let $q;
let page;
let render;
let scroll;
let resource;

function JobsIndexController (
    _resource_,
    _page_,
    _scroll_,
    _render_,
    _$scope_,
    _$compile_,
    _$q_
) {
    vm = this || {};

    $compile = _$compile_;
    $scope = _$scope_;
    $q = _$q_;
    resource = _resource_;

    page = _page_;
    scroll = _scroll_;
    render = _render_;

    // Development helper(s)
    vm.clear = devClear;

    // Stdout Navigation
    vm.scroll = {
        showBackToTop: false,
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
    vm.stream = {
        active: false,
        rendering: false,
        paused: false
    };

    const stream = false; // TODO: Set in route

    render.requestAnimationFrame(() => init());
}

function init (stream) {
    page.init(resource);

    render.init({
        get: () => resource.model.get(`related.${resource.related}.results`),
        compile: html => $compile(html)($scope)
    });

    scroll.init({
        isAtRest: scrollIsAtRest,
        previous,
        next
    });

    if (stream) {
        $scope.$on(resource.ws.namespace, process);
    } else {
        next();
    }
}

function process (scope, data) {
    if (data.event === JOB_START) {
        vm.stream.active = true;
        scroll.lock();
    } else if (data.event === JOB_END) {
        vm.stream.active = false;
    }

    const pageAdded = page.addToBuffer(data);

    if (pageAdded && !scroll.isLocked()) {
        vm.stream.paused = true;
    }

    if (vm.stream.paused && scroll.isLocked()) {
        vm.stream.paused = false;
    }

    if (vm.stream.rendering || vm.stream.paused) {
        return;
    }

    const events = page.emptyBuffer();

    return renderStream(events);
}

function renderStream (events) {
    vm.stream.rendering = true;

    return shift()
        .then(() => append(events))
        .then(() => {
            if (scroll.isLocked()) {
                scroll.setScrollPosition(scroll.getScrollHeight());
            }

            if (!vm.stream.active) {
                const buffer = page.emptyBuffer();

                if (buffer.length) {
                    return renderStream(buffer);
                } else {
                    vm.stream.rendering = false;
                    scroll.unlock();
                }
            } else {
                vm.stream.rendering = false;
            }
        });
}

function devClear () {
    init(true);
    render.clear();
}

function next () {
    return page.next()
        .then(events => {
            if (!events) {
                return;
            }

            return shift()
                .then(() => append(events));
        });
}

function previous () {
    let initialPosition = scroll.getScrollPosition();
    let postPopHeight;

    return page.previous()
        .then(events => {
            if (!events) {
                return;
            }

            return pop()
                .then(() => {
                    postPopHeight = scroll.getScrollHeight();

                    return prepend(events);
                })
                .then(()  => {
                    const currentHeight = scroll.getScrollHeight();

                    scroll.setScrollPosition(currentHeight - postPopHeight + initialPosition);
                });
        });
}

function append (events) {
    return render.append(events)
        .then(count => {
            page.updateLineCount('current', count);
        });
}

function prepend (events) {
    return render.prepend(events)
        .then(count => {
            page.updateLineCount('current', count);
        });
}

function pop () {
    if (!page.isOverCapacity()) {
        return $q.resolve();
    }

    const lines = page.trim('right');

    return render.pop(lines);
}

function shift () {
    if (!page.isOverCapacity()) {
        return $q.resolve();
    }

    const lines = page.trim('left');

    return render.shift(lines);
}

function expand () {
    vm.toggle(parent, true);
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

function scrollHome () {
    scroll.pause();

    return page.first()
        .then(events => {
            if (!events) {
                return;
            }

            return render.clear()
                .then(() => render.prepend(events))
                .then(() => {
                    scroll.setScrollPosition(0);
                    scroll.resume();
                });
        });
}

function scrollEnd () {
    if (scroll.isLocked()) {
        page.bookmark();
        scroll.unlock();

        return;
    } else if (!scroll.isLocked() && vm.stream.active) {
        page.bookmark();
        scroll.lock();

        return;
    }

    scroll.pause();

    return page.last()
        .then(events => {
            if (!events) {
                return;
            }

            return render.clear()
                .then(() => render.append(events))
                .then(() => {
                    scroll.setScrollPosition(scroll.getScrollHeight());
                    scroll.resume();
                });
        });
}

function scrollPageUp () {
    scroll.pageUp();
}

function scrollPageDown () {
    scroll.pageDown();
}

function scrollIsAtRest (isAtRest) {
    vm.scroll.showBackToTop = !isAtRest;
}

JobsIndexController.$inject = [
    'resource',
    'JobPageService',
    'JobScrollService',
    'JobRenderService',
    '$scope',
    '$compile',
    '$q'
];

module.exports = JobsIndexController;
