/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import route from './job-detail.route';
import controller from './job-detail.controller';
import service from './job-detail.service';
import hostEvents from './host-events/main';
import hostEvent from './host-event/main';
import hostSummary from './host-summary/main';

export default
    angular.module('jobDetail', [
    	hostEvents.name,
    	hostEvent.name,
    	hostSummary.name
    	])
        .controller('JobDetailController', controller)
        .service('JobDetailService', service)
        // .run(['$stateExtender', function($stateExtender) {
        //     $stateExtender.addState(route);
        // }]);
