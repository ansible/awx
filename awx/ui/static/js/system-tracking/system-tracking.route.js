/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {searchDateRange} from './search-date-range';
import moment from 'tower/shared/moment/moment';

export default {
    name: 'systemTracking',
    route: '/inventories/:inventory/system-tracking/:hosts',
    controller: 'systemTracking',
    templateUrl: '/static/js/system-tracking/system-tracking.partial.html',
    reloadOnSearch: false,
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
                            then(function(factDataAndModules) {
                                var moduleOptions = factDataAndModules[0];
                                var factResponses = factDataAndModules[1];
                                var factData = _.pluck(factResponses, 'fact');

                                factData.leftSearchRange = leftDate;
                                factData.rightSearchRange = rightDate;

                                factData.leftScanDate = moment(factResponses[0].timestamp);
                                factData.rightScanDate = moment(factResponses[1].timestamp);

                                factData.moduleName = moduleParam;
                                factData.moduleOptions = moduleOptions;

                                return factData;
                            }, true)
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
