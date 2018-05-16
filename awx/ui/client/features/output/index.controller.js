let $compile;
let $q;
let $scope;
let page;
let render;
let resource;
let scroll;
let engine;
let status;

let vm;
let streaming;
let listeners = [];

function JobsIndexController (
    _resource_,
    _page_,
    _scroll_,
    _render_,
    _engine_,
    _$scope_,
    _$compile_,
    _$q_,
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
    vm.expanded = false;
    vm.toggleExpanded = toggleExpanded;

    // Panel
    vm.resource = resource;
    vm.title = resource.model.get('name');

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
            status.setJobStatus('running');
        },
        onStop () {
            stopListening();
            status.updateStats();
            status.dispatch();
        }
    });

    streaming = false;
    return next().then(() => startListening());
}

function stopListening () {
    listeners.forEach(deregister => deregister());
    listeners = [];
}

function startListening () {
    stopListening();
    listeners.push($scope.$on(resource.ws.events, (scope, data) => handleJobEvent(data)));
    listeners.push($scope.$on(resource.ws.status, (scope, data) => handleStatusEvent(data)));
}

function handleStatusEvent (data) {
    status.pushStatusEvent(data);
}

function handleJobEvent (data) {
    streaming = streaming || attachToRunningJob();
    streaming.then(() => {
        engine.pushJobEvent(data);
        status.pushJobEvent(data);
    });
}

function attachToRunningJob () {
    if (!status.state.running) {
        return $q.resolve();
    }

    return page.last()
        .then(events => {
            if (!events) {
                return $q.resolve();
            }

            const minLine = 1 + Math.max(...events.map(event => event.end_line));

            return render.clear()
                .then(() => engine.setMinLine(minLine));
        });
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

function append (events, eng) {
    return render.append(events)
        .then(count => {
            page.updateLineCount(count, eng);
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
                .then(() => append(events));
        })
        .then(() => {
            scroll.setScrollPosition(scroll.getScrollHeight());
            scroll.resume();
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

function toggleExpanded () {
    vm.expanded = !vm.expanded;
}

function devClear () {
    render.clear().then(() => init());
}

// function showHostDetails (id) {
//     jobEvent.request('get', id)
//         .then(() => {
//             const title = jobEvent.get('host_name');

//             vm.host = {
//                 menu: true,
//                 stdout: jobEvent.get('stdout')
//             };

//             $scope.jobs.modal.show(title);
//         });
// }

// function toggle (uuid, menu) {
//     const lines = $(`.child-of-${uuid}`);
//     let icon = $(`#${uuid} .at-Stdout-toggle > i`);

//     if (menu || record[uuid].level === 1) {
//         vm.isExpanded = !vm.isExpanded;
//     }

//     if (record[uuid].children) {
//         icon = icon.add($(`#${record[uuid].children.join(', #')}`)
//             .find('.at-Stdout-toggle > i'));
//     }

//     if (icon.hasClass('fa-angle-down')) {
//         icon.addClass('fa-angle-right');
//         icon.removeClass('fa-angle-down');

//         lines.addClass('hidden');
//     } else {
//         icon.addClass('fa-angle-down');
//         icon.removeClass('fa-angle-right');

//         lines.removeClass('hidden');
//     }
// }

JobsIndexController.$inject = [
    'resource',
    'JobPageService',
    'JobScrollService',
    'JobRenderService',
    'JobEventEngine',
    '$scope',
    '$compile',
    '$q',
    'JobStatusService',
];

module.exports = JobsIndexController;
