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

    if (capacity >= events.length) {
        return slide.pushFront(events);
    }

    delete render.record;

    render.record = {};

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
        .then(changed => {
            if (changed[0] !== 0 || changed[1] !== 0) {
                const currentHeight = scroll.getScrollHeight();
                scroll.setScrollPosition((currentHeight / 4) - initialPosition);
            }

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

function compile (html) {
    return $compile(html)($scope);
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
    vm.strings = strings;
    vm.resource = resource;
    vm.title = $filter('sanitize')(resource.model.get('name'));

    vm.expanded = false;
    vm.showHostDetails = showHostDetails;
    vm.toggleExpanded = () => { vm.expanded = !vm.expanded; };

    // Stdout Navigation
    vm.menu = {
        end: last,
        home: first,
        up: previous,
        down: next,
    };

    render.requestAnimationFrame(() => {
        bufferInit();

        status.init(resource);
        slide.init(render, resource.events);

        render.init({ compile });
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
