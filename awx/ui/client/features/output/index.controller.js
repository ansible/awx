/* eslint camelcase: 0 */
import {
    EVENT_START_PLAY,
    EVENT_START_TASK,
    OUTPUT_PAGE_SIZE,
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

let lockFrames;
function onFrames (events) {
    if (lockFrames) {
        events.forEach(bufferAdd);
        return $q.resolve();
    }

    events = slide.pushFrames(events);
    const popCount = events.length - slide.getCapacity();
    const isAttached = events.length > 0;

    if (!isAttached) {
        stopFollowing();
        return $q.resolve();
    }

    if (!vm.isFollowing && canStartFollowing()) {
        startFollowing();
    }

    if (!vm.isFollowing && popCount > 0) {
        return $q.resolve();
    }

    scroll.pause();

    if (vm.isFollowing) {
        scroll.scrollToBottom();
    }

    return slide.popBack(popCount)
        .then(() => {
            if (vm.isFollowing) {
                scroll.scrollToBottom();
            }

            return slide.pushFront(events);
        })
        .then(() => {
            if (vm.isFollowing) {
                scroll.scrollToBottom();
            }

            scroll.resume();

            return $q.resolve();
        });
}

function first () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    stopFollowing();

    return slide.getFirst()
        .then(() => {
            scroll.resetScrollPosition();
        })
        .finally(() => {
            scroll.resume();
            lockFrames = false;
        });
}

function next () {
    if (vm.isFollowing) {
        scroll.scrollToBottom();

        return $q.resolve();
    }

    if (scroll.isPaused()) {
        return $q.resolve();
    }

    if (slide.getTailCounter() >= slide.getMaxCounter()) {
        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    return slide.getNext()
        .finally(() => {
            scroll.resume();
            lockFrames = false;
        });
}

function previous () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    stopFollowing();

    const initialPosition = scroll.getScrollPosition();

    return slide.getPrevious()
        .then(popHeight => {
            const currentHeight = scroll.getScrollHeight();
            scroll.setScrollPosition(currentHeight - popHeight + initialPosition);

            return $q.resolve();
        })
        .finally(() => {
            scroll.resume();
            lockFrames = false;
        });
}

function last () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    return slide.getLast()
        .then(() => {
            stream.setMissingCounterThreshold(slide.getTailCounter() + 1);
            scroll.scrollToBottom();

            return $q.resolve();
        })
        .finally(() => {
            scroll.resume();
            lockFrames = false;
        });
}

let followOnce;
let lockFollow;
function canStartFollowing () {
    if (lockFollow) {
        return false;
    }

    if (slide.isOnLastPage() && scroll.isBeyondLowerThreshold()) {
        followOnce = false;

        return true;
    }

    if (followOnce && // one-time activation from top of first page
        scroll.isBeyondUpperThreshold() &&
        slide.getHeadCounter() === 1 &&
        slide.getTailCounter() >= OUTPUT_PAGE_SIZE) {
        followOnce = false;

        return true;
    }

    return false;
}

function startFollowing () {
    if (vm.isFollowing) {
        return;
    }

    vm.isFollowing = true;
    vm.followTooltip = vm.strings.get('tooltips.MENU_FOLLOWING');
}

function stopFollowing () {
    if (!vm.isFollowing) {
        return;
    }

    vm.isFollowing = false;
    vm.followTooltip = vm.strings.get('tooltips.MENU_LAST');
}

function menuLast () {
    if (vm.isFollowing) {
        lockFollow = true;
        stopFollowing();

        return $q.resolve();
    }

    lockFollow = false;

    if (slide.isOnLastPage()) {
        scroll.scrollToBottom();

        return $q.resolve();
    }

    return last();
}

function down () {
    scroll.moveDown();
}

function up () {
    scroll.moveUp();
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

let streaming;
function stopListening () {
    streaming = null;

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

function handleJobEvent (data) {
    streaming = streaming || resource.events
        .getRange([Math.max(0, data.counter - 50), data.counter + 50])
        .then(results => {
            results.push(data);

            const counters = results.map(({ counter }) => counter);
            const min = Math.min(...counters);
            const max = Math.max(...counters);

            const missing = [];
            for (let i = min; i <= max; i++) {
                if (counters.indexOf(i) < 0) {
                    missing.push(i);
                }
            }

            if (missing.length > 0) {
                const maxMissing = Math.max(...missing);
                results = results.filter(({ counter }) => counter > maxMissing);
            }

            stream.setMissingCounterThreshold(max);
            results.forEach(item => {
                stream.pushJobEvent(item);
                status.pushJobEvent(item);
            });

            return $q.resolve();
        });

    streaming
        .then(() => {
            stream.pushJobEvent(data);
            status.pushJobEvent(data);
        });
}

function handleStatusEvent (data) {
    status.pushStatusEvent(data);
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
    vm.toggleMenuExpand = toggleMenuExpand;
    vm.toggleLineExpand = toggleLineExpand;
    vm.showHostDetails = showHostDetails;
    vm.toggleLineEnabled = resource.model.get('type') === 'job';
    vm.followTooltip = vm.strings.get('tooltips.MENU_LAST');

    render.requestAnimationFrame(() => {
        bufferInit();

        status.init(resource);
        slide.init(render, resource.events, scroll);
        render.init({ compile, toggles: vm.toggleLineEnabled });

        scroll.init({
            next,
            previous,
            onThresholdLeave () {
                followOnce = false;
                lockFollow = false;
                stopFollowing();

                return $q.resolve();
            },
        });

        stream.init({
            bufferAdd,
            bufferEmpty,
            onFrames,
            onStop () {
                lockFollow = true;
                stopFollowing();
                stopListening();
                status.updateStats();
                status.dispatch();
                status.sync();
                scroll.stop();
            }
        });

        if (resource.model.get('event_processing_finished')) {
            followOnce = false;
            lockFollow = true;
            lockFrames = true;
            stopListening();
        } else {
            followOnce = true;
            lockFollow = false;
            lockFrames = false;
            resource.events.clearCache();
            status.subscribe(data => { vm.status = data.status; });
            startListening();
        }

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
