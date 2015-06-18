/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default {
    name: 'systemTracking',
    route: '/inventories/:inventory/system-tracking/:hosts',
    controller: 'systemTracking',
    templateUrl: '/static/js/system-tracking/system-tracking.partial.html',
    reloadOnSearch: false,
    resolve: {
            moduleOptions:
                [   'getModuleOptions',
                    'lodashAsPromised',
                    '$route',
                    function(getModuleOptions, _, $route) {
                    var hostIds = $route.current.params.hosts.split(',');

                    var data =
                        getModuleOptions(hostIds[0])
                            .value();

                    return data;

                    }
                ],
            inventory:
            [   '$route',
                '$q',
                'Rest',
                'GetBasePath',
                function($route, $q, rest, getBasePath) {
                    if ($route.current.hasModelKey('inventory')) {
                        return $q.when($route.current.params.model.inventory);
                    }

                    var inventoryId = $route.current.params.inventory;

                    var url = getBasePath('inventory') + inventoryId + '/';
                    rest.setUrl(url);
                    return rest.get()
                            .then(function(data) {
                                return data.data;
                            });
                }
            ],
            hosts:
            [   '$route',
                '$q',
                'Rest',
                'GetBasePath',
                function($route, $q, rest, getBasePath) {
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
                                    });
                        });

                    return $q.all(hosts);
                }

            ]
    }
};
