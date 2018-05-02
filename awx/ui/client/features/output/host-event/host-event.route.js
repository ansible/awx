const HostEventModalTemplate = require('~features/output/host-event/host-event-modal.partial.html');
const HostEventCodeMirrorTemplate = require('~features/output/host-event/host-event-codemirror.partial.html');
const HostEventStdoutTemplate = require('~features/output/host-event/host-event-stdout.partial.html');
const HostEventStderrTemplate = require('~features/output/host-event/host-event-stderr.partial.html');

function exit () {
    // close the modal
    // using an onExit event to handle cases where the user navs away
    // using the url bar / back and not modal "X"
    $('#HostEvent').modal('hide');
    // hacky way to handle user browsing away via URL bar
    $('.modal-backdrop').remove();
    $('body').removeClass('modal-open');
}

function HostEventResolve (HostEventService, $stateParams) {
    return HostEventService.getRelatedJobEvents($stateParams.id, $stateParams.type, {
        id: $stateParams.eventId
    }).then((response) => response.data.results[0]);
}

HostEventResolve.$inject = [
    'HostEventService',
    '$stateParams',
];

const hostEventModal = {
    name: 'output.host-event',
    url: '/host-event/:eventId',
    controller: 'HostEventsController',
    templateUrl: HostEventModalTemplate,
    abstract: false,
    ncyBreadcrumb: {
        skip: true
    },
    resolve: {
        hostEvent: HostEventResolve
    },
    onExit: exit
};

const hostEventJson = {
    name: 'output.host-event.json',
    url: '/json',
    controller: 'HostEventsController',
    templateUrl: HostEventCodeMirrorTemplate,
    ncyBreadcrumb: {
        skip: true
    },
};

const hostEventStdout = {
    name: 'output.host-event.stdout',
    url: '/stdout',
    controller: 'HostEventsController',
    templateUrl: HostEventStdoutTemplate,
    ncyBreadcrumb: {
        skip: true
    },
};

const hostEventStderr = {
    name: 'output.host-event.stderr',
    url: '/stderr',
    controller: 'HostEventsController',
    templateUrl: HostEventStderrTemplate,
    ncyBreadcrumb: {
        skip: true
    },
};

export { hostEventJson, hostEventModal, hostEventStdout, hostEventStderr };
