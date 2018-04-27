import {
    hostEventModal,
    hostEventJson,
    hostEventStdout,
    hostEventStderr
} from './host-event.route';
import controller from './host-event.controller';
import service from './host-event.service';

const MODULE_NAME = 'hostEvents';

function hostEventRun ($stateExtender) {
    $stateExtender.addState(hostEventModal);
    $stateExtender.addState(hostEventJson);
    $stateExtender.addState(hostEventStdout);
    $stateExtender.addState(hostEventStderr);
}
hostEventRun.$inject = [
    '$stateExtender'
];

angular.module(MODULE_NAME, [])
    .controller('HostEventsController', controller)
    .service('HostEventService', service)
    .run(hostEventRun);
export default MODULE_NAME;
