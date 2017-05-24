/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../../shared/template-url/template-url.factory';

var hostEventModal = {
    name: 'jobResult.host-event',
    url: '/host-event/:eventId',
    controller: 'HostEventController',
    templateUrl: templateUrl('job-results/host-event/host-event-modal'),
    'abstract': false,
    ncyBreadcrumb: {
        skip: true
    },
    resolve: {
        hostEvent: ['jobResultsService', '$stateParams', function(jobResultsService, $stateParams) {
            return jobResultsService.getRelatedJobEvents($stateParams.id, {
                id: $stateParams.eventId
            }).then(function(res) {
                return res.data.results[0]; });
        }]
    },
    onExit: function() {
        // close the modal
        // using an onExit event to handle cases where the user navs away using the url bar / back and not modal "X"
        $('#HostEvent').modal('hide');
        // hacky way to handle user browsing away via URL bar
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
    }
};

var hostEventJson = {
    name: 'jobResult.host-event.json',
    url: '/json',
    controller: 'HostEventController',
    templateUrl: templateUrl('job-results/host-event/host-event-codemirror'),
    ncyBreadcrumb: {
        skip: true
    },
};

var hostEventStdout = {
    name: 'jobResult.host-event.stdout',
    url: '/stdout',
    controller: 'HostEventController',
    templateUrl: templateUrl('job-results/host-event/host-event-stdout'),
    ncyBreadcrumb: {
        skip: true
    },
};

var hostEventStderr = {
    name: 'jobResult.host-event.stderr',
    url: '/stderr',
    controller: 'HostEventController',
    templateUrl: templateUrl('job-results/host-event/host-event-stderr'),
    ncyBreadcrumb: {
        skip: true
    },
};


export { hostEventJson, hostEventModal, hostEventStdout, hostEventStderr };
