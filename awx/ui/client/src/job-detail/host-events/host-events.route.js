/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail.host-events',
    url: '/host-events/:hostName?:filter',
    controller: 'HostEventsController',
    params: {
        page_size: 10
    },
    templateUrl: templateUrl('job-detail/host-events/host-events'),
    onExit: function(){
        // close the modal
        // using an onExit event to handle cases where the user navs away using the url bar / back and not modal "X"
        $('#HostEvents').modal('hide');
        // hacky way to handle user browsing away via URL bar
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
