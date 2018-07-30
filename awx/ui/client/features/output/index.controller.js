/* eslint camelcase: 0 */
import {
    EVENT_START_PLAY,
    EVENT_START_TASK,
} from './constants';

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

let attached = false;
let noframes = false;
let isOnLastPage = false;

function onFrames (events) {
    if (noframes) {
        return $q.resolve();
    }

    if (!attached) {
        const minCounter = Math.min(...events.map(({ counter }) => counter));

        if (minCounter > slide.getTailCounter() + 1) {
            return $q.resolve();
        }

        attached = true;
    }

    if (vm.isInFollowMode) {
        vm.isFollowing = true;
    }

    const capacity = slide.getCapacity();

    if (capacity <= 0 && !isOnLastPage) {
        attached = false;

        return $q.resolve();
    }

    return slide.popBack(events.length - capacity)
        .then(() => slide.pushFront(events))
        .then(() => {
            if (vm.isFollowing && scroll.isBeyondLowerThreshold()) {
                scroll.scrollToBottom();
            }

            return $q.resolve();
        });
}

function first () {
    scroll.pause();
    unfollow();

    attached = false;
    noframes = true;
    isOnLastPage = false;

    slide.getFirst()
        .then(() => {
            scroll.resume();
            noframes = false;

            return $q.resolve();
        });
}

function next () {
    if (vm.isFollowing) {
        return $q.resolve();
    }

    scroll.pause();

    return slide.getNext()
        .then(() => {
            isOnLastPage = slide.isOnLastPage();
            if (isOnLastPage) {
                stream.setMissingCounterThreshold(slide.getTailCounter() + 1);
                if (scroll.isBeyondLowerThreshold()) {
                    scroll.scrollToBottom();
                    follow();
                }
            }
        })
        .finally(() => scroll.resume());
}

function previous () {
    scroll.pause();

    const initialPosition = scroll.getScrollPosition();
    isOnLastPage = false;

    return slide.getPrevious()
        .then(popHeight => {
            const currentHeight = scroll.getScrollHeight();
            scroll.setScrollPosition(currentHeight - popHeight + initialPosition);

            return $q.resolve();
        })
        .finally(() => scroll.resume());
}

function menuLast () {
    if (vm.isFollowing) {
        unfollow();

        return $q.resolve();
    }

    if (isOnLastPage) {
        scroll.scrollToBottom();

        return $q.resolve();
    }

    return last();
}

function last () {
    scroll.pause();

    return slide.getLast()
        .then(() => {
            stream.setMissingCounterThreshold(slide.getTailCounter() + 1);
            scroll.setScrollPosition(scroll.getScrollHeight());

            isOnLastPage = true;
            follow();
            scroll.resume();

            return $q.resolve();
        });
}

function down () {
    scroll.moveDown();
}

function up () {
    scroll.moveUp();
}

function follow () {
    isOnLastPage = slide.isOnLastPage();

    if (resource.model.get('event_processing_finished')) return;
    if (!isOnLastPage) return;

    vm.isInFollowMode = true;
}

function unfollow () {
    vm.isInFollowMode = false;
    vm.isFollowing = false;
}

function togglePanelExpand () {
    vm.isPanelExpanded = !vm.isPanelExpanded;
}

function toggleMenuExpand () {
    if (scroll.isPaused()) return;

    const recordList = Object.keys(render.record).map(key => render.record[key]);
    const playRecords = recordList.filter(({ name }) => name === EVENT_START_PLAY);
    const playIds = playRecords.map(({ uuid }) => uuid);

    // get any task record that does not have a parent play record
    const orphanTaskRecords = recordList
        .filter(({ name }) => name === EVENT_START_TASK)
        .filter(({ parents }) => !parents.some(uuid => playIds.indexOf(uuid) >= 0));

    const toggled = playRecords.concat(orphanTaskRecords)
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

function reloadState (params) {
    params.isPanelExpanded = vm.isPanelExpanded;

    return $state.transitionTo($state.current, params, { inherit: false, location: 'replace' });
}

function getMaxCounter () {
    const apiMax = resource.events.getMaxCounter();
    const wsMax = stream.getMaxCounter();

    return Math.max(apiMax, wsMax);
}

function OutputIndexController (
    _$compile_,
    _$q_,
    _$scope_,
    _$state_,
    _resource_,
    _scroll_,
    _page_,
    _render_,
    _status_,
    _slide_,
    _stream_,
    $filter,
    strings,
    $stateParams,
) {
    const { isPanelExpanded } = $stateParams;

    $compile = _$compile_;
    $q = _$q_;
    $scope = _$scope_;
    $state = _$state_;

    resource = _resource_;
    scroll = _scroll_;
    render = _render_;
    status = _status_;
    stream = _stream_;
    slide = resource.model.get('event_processing_finished') ? _page_ : _slide_;

    vm = this || {};

    // Panel
    vm.title = $filter('sanitize')(resource.model.get('name'));
    vm.status = resource.model.get('status');
    vm.strings = strings;
    vm.resource = resource;
    vm.reloadState = reloadState;
    vm.isPanelExpanded = isPanelExpanded;
    vm.togglePanelExpand = togglePanelExpand;

    // Stdout Navigation
    vm.menu = { last: menuLast, first, down, up };
    vm.isMenuExpanded = true;
    vm.isFollowing = false;
    vm.isInFollowMode = false;
    vm.toggleMenuExpand = toggleMenuExpand;
    vm.toggleLineExpand = toggleLineExpand;
    vm.showHostDetails = showHostDetails;
    vm.toggleLineEnabled = resource.model.get('type') === 'job';

    render.requestAnimationFrame(() => {
        bufferInit();

        status.init(resource);
        slide.init(render, resource.events, scroll, { getMaxCounter });
        render.init({ compile, toggles: vm.toggleLineEnabled });

        scroll.init({
            next,
            previous,
            onLeaveLower () {
                unfollow();
                return $q.resolve();
            },
            onEnterLower () {
                follow();
                return $q.resolve();
            },
        });

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
        status.subscribe(data => { vm.status = data.status; });

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
    'OutputPageService',
    'OutputRenderService',
    'OutputStatusService',
    'OutputSlideService',
    'OutputStreamService',
    '$filter',
    'OutputStrings',
    '$stateParams',
];

module.exports = OutputIndexController;
