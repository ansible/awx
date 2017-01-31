/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';

export default {
    name: 'systemTracking',
    route: '/inventories/:inventoryId/system-tracking/:hostIds',
    controller: 'systemTracking',
    templateUrl: templateUrl('system-tracking/system-tracking'),
    params: {hosts: null, inventory: null},
    reloadOnSearch: false,
    ncyBreadcrumb: {
        label: N_("SYSTEM TRACKING")
    },
    resolve: {
            moduleOptions:
                [   'getModuleOptions',
                    'ProcessErrors',
                    '$stateParams',
                    function(getModuleOptions, ProcessErrors, $stateParams) {

                    var hostIds = $stateParams.hostIds.split(',');

                    var data =
                        getModuleOptions(hostIds[0])
                            .catch(function (response) {
                                ProcessErrors(null, response.data, response.status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to get license info. GET returned status: ' +
                                    response.status
                                });
                            })
                            .value();

                    return data;

                    }
                ],
            inventory:
            [   '$stateParams',
                '$q',
                'Rest',
                'GetBasePath',
                'ProcessErrors',
                function($stateParams, $q, rest, getBasePath, ProcessErrors) {

                    if ($stateParams.inventory) {
                        return $q.when($stateParams.inventory);
                    }

                    var inventoryId = $stateParams.inventoryId;

                    var url = getBasePath('inventory') + inventoryId + '/';
                    rest.setUrl(url);
                    return rest.get()
                            .then(function(data) {
                                return data.data;
                            }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get license info. GET returned status: ' +
                    response.status
                });
            });
                }
            ],
            hosts:
            [   '$stateParams',
                '$q',
                'Rest',
                'GetBasePath',
                'ProcessErrors',
                function($stateParams, $q, rest, getBasePath, ProcessErrors) {
                    if ($stateParams.hosts) {
                        return $q.when($stateParams.hosts);
                    }

                    var hostIds = $stateParams.hostIds.split(',');

                    var hosts =
                        hostIds.map(function(hostId) {
                            var url = getBasePath('hosts') +
                                hostId + '/';

                            rest.setUrl(url);
                            return rest.get()
                                    .then(function(data) {
                                        return data.data;
                                    }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get license info. GET returned status: ' +
                    response.status
                });
            });
                        });

                    return $q.all(hosts);
                }

            ]
    }
};
