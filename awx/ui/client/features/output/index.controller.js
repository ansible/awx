let vm;
let $compile;
let $scope;
let $q;
let page;
let render;
let scroll;
let stream;
let resource;
let $state;
let qs;

let chain;
let chainLength;

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

    // search
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

    render.requestAnimationFrame(() => init());
}

function init (pageMode) {
    page.init({
        resource
    });

    render.init({
        get: () => resource.model.get(`related.${resource.related}.results`),
        compile: html => $compile(html)($scope)
    });

    scroll.init({
        isAtRest: scrollIsAtRest,
        previous,
        next
    });

    stream.init({
        page,
        scroll,
        resource,
        render: events => shift().then(() => append(events, true)),
        listen: (namespace, listener) => {
            $scope.$on(namespace, (scope, data) => listener(data));
        }
    });

    if (pageMode) {
        next();
    }
}

function devClear (pageMode) {
    init(pageMode);
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
    scroll.pause();

    return page.first()
        .then(events => {
            if (!events) {
                return;
            }

            return render.clear()
                .then(() => prepend(events))
                .then(() => {
                    scroll.resetScrollPosition();
                    scroll.resume();
                });
        });
}

function scrollEnd () {
    if (stream.isActive()) {
        if (stream.isPaused()) {
            stream.resume();
        } else {
            stream.pause();
        }

        return;
    }

    scroll.pause();

    return page.last()
        .then(events => {
            if (!events) {
                return;
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
    scroll.pageUp();
}

function scrollPageDown () {
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

function getCurrentQueryset() {
    const { job_event_search } = $state.params;

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
];

module.exports = JobsIndexController;
