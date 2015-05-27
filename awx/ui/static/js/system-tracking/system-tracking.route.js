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

                    var leftDate = searchDateRange('2015-05-26');
                    var rightDate = searchDateRange('2015-05-26');

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
                    if ($route.current.params.inventory) {
                        return $q.when(true);
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
            filters:
            [   '$route',
                '$q',
                'Rest',
                'GetBasePath',
                function($route, $q, rest, getBasePath) {
                    if ($route.current.params.hosts) {
                        return $q.when(true);
                    }

                    var hostIds = $route.current.params.filters.split(',');

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
