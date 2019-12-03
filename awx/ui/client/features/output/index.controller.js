/* eslint camelcase: 0 */
import {
    EVENT_START_PLAY,
    EVENT_START_TASK,
    OUTPUT_ELEMENT_LAST,
    OUTPUT_PAGE_SIZE,
} from './constants';

let $q;
let $scope;
let $state;

let resource;
let render;
let scroll;
let status;
let slide;
let stream;
let page;

let vm;
const listeners = [];
let lockFrames = false;

function onFrames (events) {
    events = slide.pushFrames(events);

    if (lockFrames) {
        return $q.resolve();
    }

    const popCount = events.length - render.getCapacity();

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

    return render.popBack(popCount)
        .then(() => {
            if (vm.isFollowing) {
                scroll.scrollToBottom();
            }

            return render.pushFront(events);
        })
        .then(() => {
            if (vm.isFollowing) {
                scroll.scrollToBottom();
            }

            scroll.resume();

            return $q.resolve();
        });
}

//
// Menu Controls (Running)
//

function firstRange () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    stopFollowing();
    lockFollow = true;

    if (slide.isOnFirstPage()) {
        scroll.resetScrollPosition();

        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    return render.clear()
        .then(() => slide.getFirst())
        .then(results => render.pushFront(results))
        .then(() => slide.getNext())
        .then(results => {
            const popCount = results.length - render.getCapacity();

            return render.popBack(popCount)
                .then(() => render.pushFront(results));
        })
        .finally(() => {
            render.compile();
            scroll.resume();
            lockFollow = false;
        });
}

function nextRange () {
    if (vm.isFollowing) {
        scroll.scrollToBottom();

        return $q.resolve();
    }

    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    return slide.getNext()
        .then(results => {
            const popCount = results.length - render.getCapacity();

            return render.popBack(popCount)
                .then(() => render.pushFront(results));
        })
        .finally(() => {
            render.compile();
            scroll.resume();
            lockFrames = false;

            return $q.resolve();
        });
}

function previousRange () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();
    stopFollowing();
    lockFrames = true;

    let initialPosition;
    let popHeight;

    return slide.getPrevious()
        .then(results => {
            const popCount = results.length - render.getCapacity();
            initialPosition = scroll.getScrollPosition();

            return render.popFront(popCount)
                .then(() => {
                    popHeight = scroll.getScrollHeight();

                    return render.pushBack(results);
                });
        })
        .then(() => {
            const currentHeight = scroll.getScrollHeight();
            scroll.setScrollPosition(currentHeight - popHeight + initialPosition);

            return $q.resolve();
        })
        .finally(() => {
            render.compile();
            scroll.resume();
            lockFrames = false;

            return $q.resolve();
        });
}

function lastRange () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();
    lockFrames = true;

    return render.clear()
        .then(() => slide.getLast())
        .then(results => render.pushFront(results))
        .then(() => {
            stream.setMissingCounterThreshold(slide.getTailCounter() + 1);

            scroll.scrollToBottom();
            lockFrames = false;

            return $q.resolve();
        })
        .finally(() => {
            render.compile();
            scroll.resume();

            return $q.resolve();
        });
}

function menuLastRange () {
    if (vm.isFollowing) {
        lockFollow = true;
        stopFollowing();

        return $q.resolve();
    }

    lockFollow = false;

    return lastRange()
        .then(() => {
            startFollowing();

            return $q.resolve();
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
        scroll.isBeyondUpperThreshold()) {
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

//
// Menu Controls (Page Mode)
//

function firstPage () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();

    return render.clear()
        .then(() => page.getFirst())
        .then(results => render.pushFront(results))
        .then(() => page.getNext())
        .then(results => {
            const popCount = page.trimHead();

            return render.popBack(popCount)
                .then(() => render.pushFront(results));
        })
        .finally(() => {
            render.compile();
            scroll.resume();

            return $q.resolve();
        });
}

function lastPage () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();

    return render.clear()
        .then(() => page.getLast())
        .then(results => render.pushBack(results))
        .then(() => page.getPrevious())
        .then(results => {
            const popCount = page.trimTail();

            return render.popFront(popCount)
                .then(() => render.pushBack(results));
        })
        .then(() => {
            scroll.scrollToBottom();

            return $q.resolve();
        })
        .finally(() => {
            render.compile();
            scroll.resume();

            return $q.resolve();
        });
}

function nextPage () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();

    return page.getNext()
        .then(results => {
            const popCount = page.trimHead();

            return render.popBack(popCount)
                .then(() => render.pushFront(results));
        })
        .finally(() => {
            render.compile();
            scroll.resume();
        });
}

function previousPage () {
    if (scroll.isPaused()) {
        return $q.resolve();
    }

    scroll.pause();

    let initialPosition;
    let popHeight;

    return page.getPrevious()
        .then(results => {
            const popCount = page.trimTail();
            initialPosition = scroll.getScrollPosition();

            return render.popFront(popCount)
                .then(() => {
                    popHeight = scroll.getScrollHeight();

                    return render.pushBack(results);
                });
        })
        .then(() => {
            const currentHeight = scroll.getScrollHeight();
            scroll.setScrollPosition(currentHeight - popHeight + initialPosition);

            return $q.resolve();
        })
        .finally(() => {
            render.compile();
            scroll.resume();

            return $q.resolve();
        });
}

//
// Menu Controls
//

function first () {
    if (vm.isProcessingFinished) {
        return firstPage();
    }

    return firstRange();
}

function last () {
    if (vm.isProcessingFinished) {
        return lastPage();
    }

    return lastRange()
        .then(() => previousRange());
}

function next () {
    if (vm.isProcessingFinished) {
        return nextPage();
    }

    return nextRange();
}

function previous () {
    if (vm.isProcessingFinished) {
        return previousPage();
    }

    return previousRange();
}

function menuLast () {
    if (vm.isProcessingFinished) {
        return lastPage();
    }

    return menuLastRange();
}

function down () {
    scroll.moveDown();

    if (scroll.isBeyondLowerThreshold()) {
        next();
    }
}

function up () {
    scroll.moveUp();

    if (scroll.isBeyondUpperThreshold()) {
        previous();
    }
}

function togglePanelExpand () {
    vm.isPanelExpanded = !vm.isPanelExpanded;
}

//
// Line Interaction
//

const iconCollapsed = 'fa-angle-right';
const iconExpanded = 'fa-angle-down';
const iconSelector = '.at-Stdout-toggle > i';
const lineCollapsed = 'at-Stdout-row--hidden';

function toggleCollapseAll () {
    if (scroll.isPaused()) return;

    const records = Object.keys(render.records).map(key => render.records[key]);
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

    const record = render.records[uuid];

    if (record.name === EVENT_START_PLAY) {
        togglePlayCollapse(uuid);
    }

    if (record.name === EVENT_START_TASK) {
        toggleTaskCollapse(uuid);
    }
}

function togglePlayCollapse (uuid) {
    const record = render.records[uuid];
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

        descendants
            .map(item => $(`.child-of-${item}`))
            .forEach(line => line.addClass(lineCollapsed));
    }

    descendants
        .map(item => render.records[item])
        .filter((descRecord) => descRecord && descRecord.name === EVENT_START_TASK)
        .forEach(rec => { render.records[rec.uuid].isCollapsed = true; });

    render.records[uuid].isCollapsed = !isCollapsed;
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

    render.records[uuid].isCollapsed = !isCollapsed;
}

function showHostDetails (id, uuid) {
    $state.go('output.host-event.json', { eventId: id, taskUuid: uuid });
}

function showMissingEvents (uuid) {
    const record = render.records[uuid];

    const min = Math.min(...record.counters);
    const max = Math.min(Math.max(...record.counters), min + OUTPUT_PAGE_SIZE);

    const selector = `#${uuid}`;
    const clicked = $(selector);

    return resource.events.getRange([min, max])
        .then(results => {
            const counters = results.map(({ counter }) => counter);

            for (let i = min; i <= max; i++) {
                if (counters.indexOf(i) < 0) {
                    results = results.filter(({ counter }) => counter < i);
                    break;
                }
            }

            let lines = 0;
            let untrusted = '';

            for (let i = 0; i <= results.length - 1; i++) {
                const { html, count } = render.transformEvent(results[i]);

                lines += count;
                untrusted += html;

                const shifted = render.records[uuid].counters.shift();
                delete render.uuids[shifted];
            }

            const trusted = render.trustHtml(untrusted);
            const elements = angular.element(trusted);

            return render
                .requestAnimationFrame(() => {
                    elements.insertBefore(clicked);

                    if (render.records[uuid].counters.length === 0) {
                        clicked.remove();
                        delete render.records[uuid];
                    }
                })
                .then(() => render.compile())
                .then(() => lines);
        });
}

//
// Event Handling
//

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
        .getRange([Math.max(1, data.counter - 50), data.counter + 50])
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

            results.forEach(item => {
                stream.pushJobEvent(item);
                status.pushJobEvent(item);
            });

            stream.setMissingCounterThreshold(min);

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

//
// Search
//

function reloadState (params) {
    params.isPanelExpanded = vm.isPanelExpanded;

    return $state.transitionTo($state.current, params, { inherit: false, location: 'replace' });
}

//
// Debug Mode
//

function clear () {
    stopListening();
    render.clear();

    followOnce = true;
    lockFollow = false;
    lockFrames = false;

    stream.bufferInit();
    status.init(resource);
    slide.init(resource.events, render);
    status.subscribe(data => { vm.status = data.status; });

    startListening();
}

function OutputIndexController (
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

    $q = _$q_;
    $scope = _$scope_;
    $state = _$state_;

    resource = _resource_;
    scroll = _scroll_;
    render = _render_;
    status = _status_;
    stream = _stream_;
    slide = _slide_;
    page = _page_;

    vm = this || {};

    // Panel
    vm.title = $filter('sanitize')(resource.model.get('name'));
    vm.status = resource.model.get('status');
    vm.strings = strings;
    vm.resource = resource;
    vm.reloadState = reloadState;
    vm.isPanelExpanded = isPanelExpanded;
    vm.isProcessingFinished = isProcessingFinished;
    vm.togglePanelExpand = togglePanelExpand;

    // Stdout Navigation
    vm.menu = { last: menuLast, first, down, up, clear };
    vm.isMenuCollapsed = false;
    vm.isFollowing = false;
    vm.toggleCollapseAll = toggleCollapseAll;
    vm.toggleCollapse = toggleCollapse;
    vm.showHostDetails = showHostDetails;
    vm.showMissingEvents = showMissingEvents;
    vm.toggleLineEnabled = resource.model.get('type') === 'job';
    vm.followTooltip = vm.strings.get('tooltips.MENU_LAST');
    vm.debug = _debug;

    render.requestAnimationFrame(() => {
        render.init($scope, { toggles: vm.toggleLineEnabled });

        status.init(resource);
        page.init(resource.events);
        slide.init(resource.events, render);

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
                status.updateStats();
                status.dispatch();
                status.sync();
                scroll.unlock();
                scroll.unhide();
                render.compile();
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

    $scope.$on('$destroy', () => {
        stopListening();

        render.clear();
        render.el.remove();
        slide.clear();
        stream.bufferInit();
    });
}

OutputIndexController.$inject = [
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
