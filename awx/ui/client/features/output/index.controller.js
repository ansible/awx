/* eslint camelcase: 0 */
let $compile;
let $q;
let $scope;
let $state;

let resource;
let render;
let scroll;
let status;
let slide;
let stream;

let vm;

const bufferState = [0, 0]; // [length, count]
const listeners = [];
const rx = [];

let following = false;

function bufferInit () {
    rx.length = 0;

    bufferState[0] = 0;
    bufferState[1] = 0;
}

function bufferAdd (event) {
    rx.push(event);

    bufferState[0] += 1;
    bufferState[1] += 1;

    return bufferState[1];
}

function bufferEmpty (min, max) {
    let count = 0;
    let removed = [];

    for (let i = bufferState[0] - 1; i >= 0; i--) {
        if (rx[i].counter <= max) {
            removed = removed.concat(rx.splice(i, 1));
            count++;
        }
    }

    bufferState[0] -= count;

    return removed;
}

function onFrames (events) {
    if (!following) {
        const minCounter = Math.min(...events.map(({ counter }) => counter));
        // attachment range
        const max = slide.getTailCounter() + 1;
        const min = Math.max(1, slide.getHeadCounter(), max - 50);

        if (minCounter > max || minCounter < min) {
            return $q.resolve();
        }

        follow();
    }

    const capacity = slide.getCapacity();

    return slide.popBack(events.length - capacity)
        .then(() => slide.pushFront(events))
        .then(() => {
            scroll.setScrollPosition(scroll.getScrollHeight());

            return $q.resolve();
        });
}

function first () {
    unfollow();
    scroll.pause();

    return slide.getFirst()
        .then(() => {
            scroll.resetScrollPosition();
            scroll.resume();

            return $q.resolve();
        });
}

function next () {
    return slide.slideDown();
}

function previous () {
    unfollow();

    const initialPosition = scroll.getScrollPosition();

    return slide.slideUp()
        .then(popHeight => {
            const currentHeight = scroll.getScrollHeight();
            scroll.setScrollPosition(currentHeight - popHeight + initialPosition);

            return $q.resolve();
        });
}

function last () {
    scroll.pause();

    return slide.getLast()
        .then(() => {
            stream.setMissingCounterThreshold(slide.getTailCounter() + 1);
            scroll.setScrollPosition(scroll.getScrollHeight());

            scroll.resume();

            return $q.resolve();
        });
}

function follow () {
    scroll.pause();
    // scroll.hide();

    following = true;
}

function unfollow () {
    following = false;

    // scroll.unhide();
    scroll.resume();
}

function togglePanelExpand () {
    vm.isPanelExpanded = !vm.isPanelExpanded;
}

function toggleMenuExpand () {
    if (scroll.isPaused()) return;

    const recordList = Object.keys(render.record).map(key => render.record[key]);
    const minLevel = Math.min(...recordList.map(({ level }) => level));

    const toggled = recordList
        .filter(({ level }) => level === minLevel)
        .map(({ uuid }) => getToggleElements(uuid))
        .filter(({ icon }) => icon.length > 0)
        .map(({ icon, lines }) => setExpanded(icon, lines, !vm.isMenuExpanded));

    if (toggled.length > 0) {
        vm.isMenuExpanded = !vm.isMenuExpanded;
    }
}

function toggleLineExpand (uuid) {
    if (scroll.isPaused()) return;

    const { icon, lines } = getToggleElements(uuid);
    const isExpanded = icon.hasClass('fa-angle-down');

    setExpanded(icon, lines, !isExpanded);

    vm.isMenuExpanded = !isExpanded;
}

function getToggleElements (uuid) {
    const record = render.record[uuid];
    const lines = $(`.child-of-${uuid}`);

    const iconSelector = '.at-Stdout-toggle > i';
    const additionalSelector = `#${(record.children || []).join(', #')}`;

    let icon = $(`#${uuid} ${iconSelector}`);
    if (additionalSelector) {
        icon = icon.add($(additionalSelector).find(iconSelector));
    }

    return { icon, lines };
}

function setExpanded (icon, lines, expanded) {
    if (expanded) {
        icon.removeClass('fa-angle-right');
        icon.addClass('fa-angle-down');
        lines.removeClass('hidden');
    } else {
        icon.removeClass('fa-angle-down');
        icon.addClass('fa-angle-right');
        lines.addClass('hidden');
    }
}

function compile (html) {
    return $compile(html)($scope);
}

function showHostDetails (id, uuid) {
    $state.go('output.host-event.json', { eventId: id, taskUuid: uuid });
}

function stopListening () {
    listeners.forEach(deregister => deregister());
    listeners.length = 0;
}

function startListening () {
    stopListening();

    listeners.push($scope.$on(resource.ws.events, (scope, data) => handleJobEvent(data)));
    listeners.push($scope.$on(resource.ws.status, (scope, data) => handleStatusEvent(data)));

    if (resource.model.get('type') === 'job') return;
    if (resource.model.get('type') === 'project_update') return;

    listeners.push($scope.$on(resource.ws.summary, (scope, data) => handleSummaryEvent(data)));
}

function handleStatusEvent (data) {
    status.pushStatusEvent(data);
}

function handleJobEvent (data) {
    stream.pushJobEvent(data);
    status.pushJobEvent(data);
}

function handleSummaryEvent (data) {
    if (resource.model.get('id') !== data.unified_job_id) return;
    if (!data.final_counter) return;

    stream.setFinalCounter(data.final_counter);
}

function OutputIndexController (
    _$compile_,
    _$q_,
    _$scope_,
    _$state_,
    _resource_,
    _scroll_,
    _render_,
    _status_,
    _slide_,
    _stream_,
    $filter,
    strings,
) {
    $compile = _$compile_;
    $q = _$q_;
    $scope = _$scope_;
    $state = _$state_;

    resource = _resource_;
    scroll = _scroll_;
    render = _render_;
    slide = _slide_;
    status = _status_;
    stream = _stream_;

    vm = this || {};

    // Panel
    vm.title = $filter('sanitize')(resource.model.get('name'));
    vm.strings = strings;
    vm.resource = resource;
    vm.isPanelExpanded = false;
    vm.togglePanelExpand = togglePanelExpand;

    // Stdout Navigation
    vm.menu = {
        end: last,
        home: first,
        up: previous,
        down: next,
    };
    vm.isMenuExpanded = true;
    vm.toggleMenuExpand = toggleMenuExpand;
    vm.toggleLineExpand = toggleLineExpand;
    vm.showHostDetails = showHostDetails;
    vm.toggleLineEnabled = resource.model.get('type') === 'job';

    render.requestAnimationFrame(() => {
        bufferInit();

        status.init(resource);
        slide.init(render, resource.events, scroll);

        render.init({ compile, toggles: vm.toggleLineEnabled });
        scroll.init({ previous, next });

        stream.init({
            bufferAdd,
            bufferEmpty,
            onFrames,
            onStop () {
                stopListening();
                status.updateStats();
                status.dispatch();
                unfollow();
            }
        });

        startListening();

        return last();
    });
}

OutputIndexController.$inject = [
    '$compile',
    '$q',
    '$scope',
    '$state',
    'resource',
    'OutputScrollService',
    'OutputRenderService',
    'OutputStatusService',
    'OutputSlideService',
    'OutputStreamService',
    '$filter',
    'OutputStrings',
];

module.exports = OutputIndexController;
