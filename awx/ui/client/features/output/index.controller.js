const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';
const PLAY_START = 'playbook_on_play_start';
const TASK_START = 'playbook_on_task_start';

let $compile;
let $q;
let $scope;
let $state;
let moment;
let page;
let qs;
let render;
let resource;
let scroll;
let stream;

let vm;

let eventCounter;
let statsEvent;

function JobsIndexController (
    _resource_,
    _page_,
    _scroll_,
    _render_,
    _stream_,
    _$scope_,
    _$compile_,
    _$q_,
    _$state_,
    _qs_,
    _moment_,
) {
    vm = this || {};

    $compile = _$compile_;
    $scope = _$scope_;
    $q = _$q_;
    resource = _resource_;

    page = _page_;
    scroll = _scroll_;
    render = _render_;
    stream = _stream_;

    moment = _moment_;

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

    // Search
    $state = _$state_;
    qs = _qs_;

    vm.searchValue = '';
    vm.searchRejected = null;
    vm.searchKey = false;
    vm.searchKeyExamples = searchKeyExamples;
    vm.searchKeyFields = searchKeyFields;

    vm.clearSearch = clearSearch;
    vm.search = search;
    vm.toggleSearchKey = toggleSearchKey;
    vm.removeSearchTag = removeSearchTag;
    vm.searchTags = getSearchTags(getCurrentQueryset());

    // Events
    eventCounter = null;
    statsEvent = resource.stats;

    // Status Bar
    vm.status = {
        stats: statsEvent,
        elapsed: resource.model.get('elapsed'),
        running: Boolean(resource.model.get('started')) && !resource.model.get('finished'),
        title: resource.model.get('name'),
        plays: null,
        tasks: null,
    };

    // Details
    vm.details = {
        resource,
        started: resource.model.get('started'),
        finished: resource.model.get('finished'),
        status: resource.model.get('status'),
    };

    render.requestAnimationFrame(() => init(!vm.status.running));
}

function init (pageMode) {
    page.init({
        resource,
    });

    render.init({
        get: () => resource.model.get(`related.${resource.related}.results`),
        compile: html => $compile(html)($scope),
        isStreamActive: stream.isActive
    });

    scroll.init({
        isAtRest: scrollIsAtRest,
        previous,
        next,
    });

    stream.init({
        page,
        scroll,
        resource,
        onEventFrame (events) {
            return shift().then(() => append(events, true));
        },
        onStart () {
            vm.status.plays = 0;
            vm.status.tasks = 0;
            vm.status.running = true;
        },
        onStop () {
            vm.status.stats = statsEvent;
            vm.status.running = false;

            vm.details.status = statsEvent.failed ? 'failed' : 'successful';
            vm.details.finished = statsEvent.created;
        }
    });

    $scope.$on(resource.ws.namespace, handleSocketEvent);

    if (pageMode) {
        next();
    }
}

function handleSocketEvent (scope, data) {
    const isLatest = ((!eventCounter) || (data.counter > eventCounter));

    if (isLatest) {
        eventCounter = data.counter;

        vm.details.status = _.get(data, 'summary_fields.job.status');

        vm.status.elapsed = moment(data.created)
            .diff(resource.model.get('created'), 'seconds');
    }

    if (data.event === JOB_START) {
        vm.details.started = data.created;
    }

    if (data.event === PLAY_START) {
        vm.status.plays++;
    }

    if (data.event === TASK_START) {
        vm.status.tasks++;
    }

    if (data.event === JOB_END) {
        statsEvent = data;
    }

    stream.pushEventData(data);
}

function devClear (pageMode) {
    init(pageMode);
    render.clear();
}

function next () {
    return page.next()
        .then(events => {
            if (!events) {
                return $q.resolve();
            }

            return shift()
                .then(() => append(events))
                .then(() => {
                    if (scroll.isMissing()) {
                        return next();
                    }

                    return $q.resolve();
                });
        });
}

function previous () {
    const initialPosition = scroll.getScrollPosition();
    let postPopHeight;

    return page.previous()
        .then(events => {
            if (!events) {
                return $q.resolve();
            }

            return pop()
                .then(() => {
                    postPopHeight = scroll.getScrollHeight();

                    return prepend(events);
                })
                .then(() => {
                    const currentHeight = scroll.getScrollHeight();
                    scroll.setScrollPosition(currentHeight - postPopHeight + initialPosition);
                });
        });
}

function append (events, stream) {
    return render.append(events)
        .then(count => {
            page.updateLineCount(count, stream);
        });
}

function prepend (events) {
    return render.prepend(events)
        .then(count => {
            page.updateLineCount(count);
        });
}

function pop () {
    if (!page.isOverCapacity()) {
        return $q.resolve();
    }

    const lines = page.trim();

    return render.pop(lines);
}

function shift () {
    if (!page.isOverCapacity()) {
        return $q.resolve();
    }

    const lines = page.trim(true);

    return render.shift(lines);
}

function scrollHome () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();

    return page.first()
        .then(events => {
            if (!events) {
                return $q.resolve();
            }

            return render.clear()
                .then(() => prepend(events))
                .then(() => {
                    scroll.resetScrollPosition();
                    scroll.resume();
                })
                .then(() => {
                    if (scroll.isMissing()) {
                        return next();
                    }

                    return $q.resolve();
                });
        });
}

function scrollEnd () {
    if (stream.isActive()) {
        if (stream.isTransitioning()) {
            return $q.resolve();
        }

        if (stream.isPaused()) {
            stream.resume();
        } else {
            stream.pause();
        }

        return $q.resolve();
    } else if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();

    return page.last()
        .then(events => {
            if (!events) {
                return $q.resolve();
            }

            return render.clear()
                .then(() => append(events))
                .then(() => {
                    scroll.setScrollPosition(scroll.getScrollHeight());
                    scroll.resume();
                });
        });
}

function scrollPageUp () {
    if (scroll.isPaused()) {
        return;
    }

    scroll.pageUp();
}

function scrollPageDown () {
    if (scroll.isPaused()) {
        return;
    }

    scroll.pageDown();
}

function scrollIsAtRest (isAtRest) {
    vm.scroll.showBackToTop = !isAtRest;
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

//
// Search
//

const searchReloadOptions = { reload: true, inherit: false };
const searchKeyExamples = ['id:>1', 'task:set', 'created:>=2000-01-01'];
const searchKeyFields = ['changed', 'failed', 'host_name', 'stdout', 'task', 'role', 'playbook', 'play'];

function toggleSearchKey () {
    vm.searchKey = !vm.searchKey;
}

function getCurrentQueryset () {
    const { job_event_search } = $state.params; // eslint-disable-line camelcase

    return qs.decodeArr(job_event_search);
}

function getSearchTags (queryset) {
    return qs.createSearchTagsFromQueryset(queryset)
        .filter(tag => !tag.startsWith('event'))
        .filter(tag => !tag.startsWith('-event'))
        .filter(tag => !tag.startsWith('page_size'))
        .filter(tag => !tag.startsWith('order_by'));
}

function removeSearchTag (index) {
    const searchTerm = vm.searchTags[index];

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.removeTermsFromQueryset(currentQueryset, searchTerm);

    vm.searchTags = getSearchTags(modifiedQueryset);

    $state.params.job_event_search = qs.encodeArr(modifiedQueryset);
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function search () {
    const searchInputQueryset = qs.getSearchInputQueryset(vm.searchValue);

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.mergeQueryset(currentQueryset, searchInputQueryset);

    vm.searchTags = getSearchTags(modifiedQueryset);

    $state.params.job_event_search = qs.encodeArr(modifiedQueryset);
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function clearSearch () {
    vm.searchTags = [];

    $state.params.job_event_search = '';
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

JobsIndexController.$inject = [
    'resource',
    'JobPageService',
    'JobScrollService',
    'JobRenderService',
    'JobStreamService',
    '$scope',
    '$compile',
    '$q',
    '$state',
    'QuerySet',
    'moment',
];

module.exports = JobsIndexController;
