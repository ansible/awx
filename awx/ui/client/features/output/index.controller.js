let $compile;
let $q;
let $scope;
let $state;
let page;
let qs;
let render;
let resource;
let scroll;
let engine;
let status;

let vm;

function JobsIndexController (
    _resource_,
    _page_,
    _scroll_,
    _render_,
    _engine_,
    _$scope_,
    _$compile_,
    _$q_,
    _$state_,
    _qs_,
    _status_,
) {
    vm = this || {};

    $compile = _$compile_;
    $scope = _$scope_;
    $q = _$q_;
    resource = _resource_;

    page = _page_;
    scroll = _scroll_;
    render = _render_;
    engine = _engine_;
    status = _status_;

    // Development helper(s)
    vm.clear = devClear;

    // Expand/collapse
    vm.toggle = toggle;
    vm.expand = expand;
    vm.isExpanded = true;

    // Panel
    vm.resource = resource;
    vm.title = resource.model.get('name');

    // Search
    $state = _$state_;
    qs = _qs_;

    vm.search = {
        clearSearch,
        searchKeyExamples,
        searchKeyFields,
        toggleSearchKey,
        removeSearchTag,
        submitSearch,
        value: '',
        key: false,
        rejected: false,
        disabled: !resource.model.get('finished'),
        tags: getSearchTags(getCurrentQueryset()),
    };

    // Stdout Navigation
    vm.scroll = {
        showBackToTop: false,
        home: scrollHome,
        end: scrollEnd,
        down: scrollPageDown,
        up: scrollPageUp
    };

    render.requestAnimationFrame(() => init());
}

function init () {
    status.init({
        resource,
    });

    page.init({
        resource,
    });

    render.init({
        get: () => resource.model.get(`related.${resource.related}.results`),
        compile: html => $compile(html)($scope),
        isStreamActive: engine.isActive,
    });

    scroll.init({
        isAtRest: scrollIsAtRest,
        previous,
        next,
    });

    engine.init({
        page,
        scroll,
        resource,
        onEventFrame (events) {
            return shift().then(() => append(events, true));
        },
        onStart () {
            status.resetCounts();
            status.setJobStatus('running');

            vm.search.disabled = true;
        },
        onStop () {
            status.updateStats();

            vm.search.disabled = false;
        }
    });

    $scope.$on(resource.ws.events, handleSocketEvent);
    $scope.$on(resource.ws.status, handleStatusEvent);

    if (!status.isRunning()) {
        next();
    }
}

function handleStatusEvent (scope, data) {
    status.pushStatusEvent(data);
}

function handleSocketEvent (scope, data) {
    engine.pushJobEvent(data);

    status.pushJobEvent(data);
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

function append (events, engine) {
    return render.append(events)
        .then(count => {
            page.updateLineCount(count, engine);
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
    if (engine.isActive()) {
        if (engine.isTransitioning()) {
            return $q.resolve();
        }

        if (engine.isPaused()) {
            engine.resume();
        } else {
            engine.pause();
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
    vm.search.key = !vm.search.key;
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
    const searchTerm = vm.search.tags[index];

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.removeTermsFromQueryset(currentQueryset, searchTerm);

    vm.search.tags = getSearchTags(modifiedQueryset);

    $state.params.job_event_search = qs.encodeArr(modifiedQueryset);
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function submitSearch () {
    const searchInputQueryset = qs.getSearchInputQueryset(vm.search.value);

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.mergeQueryset(currentQueryset, searchInputQueryset);

    vm.search.tags = getSearchTags(modifiedQueryset);

    $state.params.job_event_search = qs.encodeArr(modifiedQueryset);
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function clearSearch () {
    vm.search.tags = [];

    $state.params.job_event_search = '';
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

JobsIndexController.$inject = [
    'resource',
    'JobPageService',
    'JobScrollService',
    'JobRenderService',
    'JobEventEngine',
    '$scope',
    '$compile',
    '$q',
    '$state',
    'QuerySet',
    'JobStatusService',
];

module.exports = JobsIndexController;
