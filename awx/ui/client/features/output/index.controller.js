/* eslint camelcase: 0 */
import {
    EVENT_START_PLAY,
    EVENT_START_TASK,
    OUTPUT_ELEMENT_LAST,
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

const listeners = [];

let lockFrames;
function onFrames (events) {
    events = slide.pushFrames(events);

    if (lockFrames) {
        return $q.resolve();
    }

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

    scroll.unlock();
    scroll.unhide();

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

const iconCollapsed = 'fa-angle-right';
const iconExpanded = 'fa-angle-down';
const iconSelector = '.at-Stdout-toggle > i';
const lineCollapsed = 'hidden';

function toggleCollapseAll () {
    if (scroll.isPaused()) return;

    const records = Object.keys(render.record).map(key => render.record[key]);
    const plays = records.filter(({ name }) => name === EVENT_START_PLAY);
    const tasks = records.filter(({ name }) => name === EVENT_START_TASK);

    const orphanLines = records
        .filter(({ level }) => level === 3)
        .filter(({ parents }) => !records[parents[0]]);

    const orphanLineParents = orphanLines
        .map(({ parents }) => ({ uuid: parents[0] }));

    plays.concat(tasks).forEach(({ uuid }) => {
        const icon = $(`#${uuid} ${iconSelector}`);

        if (vm.isMenuCollapsed) {
            icon.removeClass(iconCollapsed);
            icon.addClass(iconExpanded);
        } else {
            icon.removeClass(iconExpanded);
            icon.addClass(iconCollapsed);
        }
    });

    tasks.concat(orphanLineParents).forEach(({ uuid }) => {
        const lines = $(`.child-of-${uuid}`);

        if (vm.isMenuCollapsed) {
            lines.removeClass(lineCollapsed);
        } else {
            lines.addClass(lineCollapsed);
        }
    });

    vm.isMenuCollapsed = !vm.isMenuCollapsed;
    render.setCollapseAll(vm.isMenuCollapsed);
}

function toggleCollapse (uuid) {
    if (scroll.isPaused()) return;

    const record = render.record[uuid];

    if (record.name === EVENT_START_PLAY) {
        togglePlayCollapse(uuid);
    }

    if (record.name === EVENT_START_TASK) {
        toggleTaskCollapse(uuid);
    }
}

function togglePlayCollapse (uuid) {
    const record = render.record[uuid];
    const descendants = record.children || [];

    const icon = $(`#${uuid} ${iconSelector}`);
    const lines = $(`.child-of-${uuid}`);
    const taskIcons = $(`#${descendants.join(', #')}`).find(iconSelector);

    const isCollapsed = icon.hasClass(iconCollapsed);

    if (isCollapsed) {
        icon.removeClass(iconCollapsed);
        icon.addClass(iconExpanded);

        taskIcons.removeClass(iconExpanded);
        taskIcons.addClass(iconCollapsed);
        lines.removeClass(lineCollapsed);

        descendants
            .map(item => $(`.child-of-${item}`))
            .forEach(line => line.addClass(lineCollapsed));
    } else {
        icon.removeClass(iconExpanded);
        icon.addClass(iconCollapsed);

        taskIcons.removeClass(iconExpanded);
        taskIcons.addClass(iconCollapsed);

        lines.addClass(lineCollapsed);
    }

    descendants
        .map(item => render.record[item])
        .filter(({ name }) => name === EVENT_START_TASK)
        .forEach(rec => { render.record[rec.uuid].isCollapsed = true; });

    render.record[uuid].isCollapsed = !isCollapsed;
}

function toggleTaskCollapse (uuid) {
    const icon = $(`#${uuid} ${iconSelector}`);
    const lines = $(`.child-of-${uuid}`);

    const isCollapsed = icon.hasClass(iconCollapsed);

    if (isCollapsed) {
        icon.removeClass(iconCollapsed);
        icon.addClass(iconExpanded);
        lines.removeClass(lineCollapsed);
    } else {
        icon.removeClass(iconExpanded);
        icon.addClass(iconCollapsed);
        lines.addClass(lineCollapsed);
    }

    render.record[uuid].isCollapsed = !isCollapsed;
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

function clear () {
    stopListening();
    render.clear();

    followOnce = true;
    lockFollow = false;
    lockFrames = false;

    stream.bufferInit();
    status.init(resource);
    slide.init(render, resource.events, scroll);
    status.subscribe(data => { vm.status = data.status; });

    startListening();
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
    const { isPanelExpanded, _debug } = $stateParams;
    const isProcessingFinished = !_debug && _resource_.model.get('event_processing_finished');

    $compile = _$compile_;
    $q = _$q_;
    $scope = _$scope_;
    $state = _$state_;

    resource = _resource_;
    scroll = _scroll_;
    render = _render_;
    status = _status_;
    stream = _stream_;
    slide = isProcessingFinished ? _page_ : _slide_;

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
    vm.menu = { last: menuLast, first, down, up, clear };
    vm.isMenuCollapsed = false;
    vm.isFollowing = false;
    vm.toggleCollapseAll = toggleCollapseAll;
    vm.toggleCollapse = toggleCollapse;
    vm.showHostDetails = showHostDetails;
    vm.toggleLineEnabled = resource.model.get('type') === 'job';
    vm.followTooltip = vm.strings.get('tooltips.MENU_LAST');
    vm.debug = _debug;

    render.requestAnimationFrame(() => {
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

        let showFollowTip = true;
        const rates = [];
        stream.init({
            onFrames,
            onFrameRate (rate) {
                rates.push(rate);
                rates.splice(0, rates.length - 5);

                if (rates.every(value => value === 1)) {
                    scroll.unlock();
                    scroll.unhide();
                }

                if (rate > 1 && vm.isFollowing) {
                    scroll.lock();
                    scroll.hide();

                    if (showFollowTip) {
                        showFollowTip = false;
                        $(OUTPUT_ELEMENT_LAST).trigger('mouseenter');
                    }
                }
            },
            onStop () {
                lockFollow = true;
                stopFollowing();
                stopListening();
                status.updateStats();
                status.dispatch();
                status.sync();
                scroll.unlock();
                scroll.unhide();
            }
        });

        if (isProcessingFinished) {
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

        if (_debug) {
            return render.clear();
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

