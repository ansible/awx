/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'systemTracking',
    route: '/inventories/:inventory/system-tracking/:hosts',
    controller: 'systemTracking',
    templateUrl: templateUrl('system-tracking/system-tracking'),
    reloadOnSearch: false,
    resolve: {
            moduleOptions:
                [   'getModuleOptions',
                    'lodashAsPromised',
                    'ProcessErrors',
                    '$state',
                    '$stateParams',
                    function(getModuleOptions, _, ProcessErrors, $state, $stateParams) {
                    var hostIds = JSON.parse($stateParams.hosts);
                    //  hostIds = hostIds.split(',');

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
            [   '$state',
                '$q',
                'Rest',
                'GetBasePath',
                'ProcessErrors',
                function($state, $q, rest, getBasePath, ProcessErrors) {

                    if ($state.current.hasModelKey('inventory')) {
                        return $q.when($state.current.params.model.inventory);
                    }

                    var inventoryId = $state.current.params.inventory;

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
            [   '$state',
                '$q',
                'Rest',
                'GetBasePath',
                'ProcessErrors',
                function($state, $q, rest, getBasePath, ProcessErrors) {
                    if ($state.current.hasModelKey('hosts')) {
                        return $q.when($state.current.params.model.hosts);
                    }

                    var hostIds = $state.current.params.hosts.split(',');

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
