function HostEventsController (
    $scope,
    $state,
    $filter,
    HostEventService,
    hostEvent,
    OutputStrings
) {
    $scope.processEventStatus = HostEventService.processEventStatus;
    $scope.processResults = processResults;
    $scope.isActiveState = isActiveState;
    $scope.getActiveHostIndex = getActiveHostIndex;
    $scope.closeHostEvent = closeHostEvent;
    $scope.strings = OutputStrings;

    const sanitize = $filter('sanitize');

    function init () {
        hostEvent.event_name = hostEvent.event;
        $scope.event = _.cloneDeep(hostEvent);

        // grab standard out & standard error if present from the host
        // event's 'res' object, for things like Ansible modules. Small
        // wrinkle in this implementation is that the stdout/stderr tabs
        // should be shown if the `res` object has stdout/stderr keys, even
        // if they're a blank string. The presence of these keys is
        // potentially significant to a user.
        if (_.has(hostEvent.event_data, 'task_action')) {
            $scope.module_name = hostEvent.event_data.task_action;
        } else if (!_.has(hostEvent.event_data, 'task_action')) {
            $scope.module_name = 'No result found';
        }

        if (_.has(hostEvent.event_data, 'res.stdout')) {
            if (hostEvent.event_data.res.stdout === '') {
                $scope.stdout = ' ';
            } else {
                $scope.stdout = sanitize(hostEvent.event_data.res.stdout);
            }
        }

        if (_.has(hostEvent.event_data, 'res.stderr')) {
            if (hostEvent.event_data.res.stderr === '') {
                $scope.stderr = ' ';
            } else {
                $scope.stderr = sanitize(hostEvent.event_data.res.stderr);
            }
        }

        if (_.has(hostEvent.event_data, 'res')) {
            $scope.json = hostEvent.event_data.res;
        }

        if ($scope.module_name === 'debug' &&
            _.has(hostEvent.event_data, 'res.result.stdout')) {
            $scope.stdout = sanitize(hostEvent.event_data.res.result.stdout);
        }
        if ($scope.module_name === 'yum' &&
            _.has(hostEvent.event_data, 'res.results') &&
            _.isArray(hostEvent.event_data.res.results)) {
            const event = hostEvent.event_data.res.results;
            $scope.stdout = sanitize(event[0]);// eslint-disable-line prefer-destructuring
        }
        // instantiate Codemirror
        if ($state.current.name === 'output.host-event.json') {
            try {
                if (_.has(hostEvent.event_data, 'res')) {
                    initCodeMirror(
                        'HostEvent-codemirror',
                        JSON.stringify($scope.json, null, 4),
                        { name: 'javascript', json: true }
                    );
                    resize();
                } else {
                    $scope.no_json = true;
                }
            } catch (err) {
                // element with id HostEvent-codemirror is not the view
                // controlled by this instance of HostEventController
            }
        } else if ($state.current.name === 'output.host-event.stdout') {
            try {
                resize();
            } catch (err) {
                // element with id HostEvent-codemirror is not the view
                // controlled by this instance of HostEventController
            }
        } else if ($state.current.name === 'output.host-event.stderr') {
            try {
                resize();
            } catch (err) {
                // element with id HostEvent-codemirror is not the view
                // controlled by this instance of HostEventController
            }
        }
        $('#HostEvent').modal('show');
        $('.modal-content').resizable({
            minHeight: 523,
            minWidth: 600
        });
        $('.modal-dialog').draggable({
            cancel: '.HostEvent-view--container'
        });

        function resize () {
            if ($state.current.name === 'output.host-event.json') {
                const editor = $('.CodeMirror')[0].CodeMirror;
                const height = $('.modal-dialog').height() - $('.HostEvent-header').height() - $('.HostEvent-details').height() - $('.HostEvent-nav').height() - $('.HostEvent-controls').height() - 120;
                editor.setSize('100%', height);
            } else if ($state.current.name === 'output.host-event.stdout' || $state.current.name === 'output.host-event.stderr') {
                const height = $('.modal-dialog').height() - $('.HostEvent-header').height() - $('.HostEvent-details').height() - $('.HostEvent-nav').height() - $('.HostEvent-controls').height() - 120;
                $('.HostEvent-stdout').width('100%');
                $('.HostEvent-stdout').height(height);
                $('.HostEvent-stdoutContainer').height(height);
                $('.HostEvent-numberColumnPreload').height(height);
            }
        }

        $('.modal-dialog').on('resize', resize);

        $('#HostEvent').on('hidden.bs.modal', $scope.closeHostEvent);
    }

    function processResults (value) {
        if (typeof value === 'object') {
            return false;
        }
        return true;
    }

    function initCodeMirror (el, data, mode) {
        const container = document.getElementById(el);
        const options = {};
        options.lineNumbers = true;
        options.mode = mode;
        options.readOnly = true;
        options.scrollbarStyle = null;
        const editor = CodeMirror.fromTextArea(// eslint-disable-line no-undef
            container,
            options
        );
        editor.setSize('100%', 200);
        editor.getDoc().setValue(data);
    }

    function isActiveState (name) {
        return $state.current.name === name;
    }

    function getActiveHostIndex () {
        function hostResultfilter (obj) {
            return obj.id === $scope.event.id;
        }
        const result = $scope.hostResults.filter(hostResultfilter);
        return $scope.hostResults.indexOf(result[0]);
    }

    function closeHostEvent () {
        // Unbind the listener so it doesn't fire when we close the modal via navigation
        $('#HostEvent').off('hidden.bs.modal');
        $('#HostEvent').modal('hide');
        $state.go('output');
    }
    $scope.init = init;
    $scope.init();
}

HostEventsController.$inject = [
    '$scope',
    '$state',
    '$filter',
    'HostEventService',
    'hostEvent',
    'OutputStrings'
];

module.exports = HostEventsController;
