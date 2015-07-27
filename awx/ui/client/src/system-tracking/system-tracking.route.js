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
                    '$route',
                    function(getModuleOptions, _, ProcessErrors, $route) {
                    var hostIds = $route.current.params.hosts.split(',');

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
            [   '$route',
                '$q',
                'Rest',
                'GetBasePath',
                'ProcessErrors',
                function($route, $q, rest, getBasePath, ProcessErrors) {
                    if ($route.current.hasModelKey('inventory')) {
                        return $q.when($route.current.params.model.inventory);
                    }

                    var inventoryId = $route.current.params.inventory;

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
            [   '$route',
                '$q',
                'Rest',
                'GetBasePath',
                'ProcessErrors',
                function($route, $q, rest, getBasePath, ProcessErrors) {
                    if ($route.current.hasModelKey('hosts')) {
                        return $q.when($route.current.params.model.hosts);
                    }

                    var hostIds = $route.current.params.hosts.split(',');

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
