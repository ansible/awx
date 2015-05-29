/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {searchDateRange} from './search-date-range';

export default {
    name: 'systemTracking',
    route: '/inventories/:inventory/system-tracking/:hosts',
    controller: 'systemTracking',
    templateUrl: '/static/js/system-tracking/system-tracking.partial.html',
    resolve: {
            factScanData:
                [   'getDataForComparison',
                    'lodashAsPromised',
                    '$route',
                    '$location',
                    function(getDataForComparison, _, $route, $location) {
                    var hostIds = $route.current.params.hosts.split(',');
                    var moduleParam = $location.search().module || 'packages';

                    var leftDate = searchDateRange('yesterday');
                    var rightDate = searchDateRange();

                    if (hostIds.length === 1) {
                        hostIds = hostIds.concat(hostIds[0]);
                    }

                    var data =
                        getDataForComparison(hostIds, moduleParam, leftDate, rightDate).
                        thenThru(function(factData) {
                                factData.leftDate = leftDate;
                                factData.rightDate = rightDate;
                                factData.moduleName = moduleParam;
                                return factData;
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
                function($route, $q, rest, getBasePath) {
                    if ($route.current.params.hasModelKey('inventory')) {
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
                    if ($route.current.params.hasModelKey('hosts')) {
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
