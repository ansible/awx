/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'activityStream',
    route: '/activity_stream?target&id',
    templateUrl: templateUrl('activity-stream/activitystream'),
    controller: 'activityStreamController',
    ncyBreadcrumb: {
        label: "ACTIVITY STREAM"
    },
    resolve: {
        subTitle:
        [   '$stateParams',
            'Rest',
            'ModelToPlural',
            'GetBasePath',
            'ProcessErrors',
            function($stateParams, rest, ModelToPlural, getBasePath, ProcessErrors) {
                // If we have a target and an ID then we want to go grab the name of the object
                // that we're examining with the activity stream.  This name will be used in the
                // subtitle.
                if ($stateParams.target && $stateParams.id) {
                    var target = $stateParams.target;
                    var id = $stateParams.id;

                    var url = getBasePath(ModelToPlural(target)) + id + '/';
                    rest.setUrl(url);
                    return rest.get()
                        .then(function(data) {
                            // Return the name or the username depending on which is available.
                            return (data.data.name || data.data.username);
                        }).catch(function (response) {
                        ProcessErrors(null, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get title info. GET returned status: ' +
                            response.status
                        });
                    });
                }
                else {
                    return null;
                }
            }
        ]
    }
};
