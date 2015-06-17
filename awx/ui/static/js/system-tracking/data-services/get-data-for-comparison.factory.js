/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import dedupeVersions from './dedupe-versions';

export default
    [   'factScanDataService',
        'getModuleOptions',
        'resolveEmptyVersions',
        'lodashAsPromised',
        function(factScanDataService, getModuleOptions, resolveEmptyVersions, _) {
            return function(hostIds, moduleName, leftDate, rightDate) {

                var singleHostMode = false;

                if (hostIds.length === 1) {
                    singleHostMode = true;
                    hostIds = hostIds.concat(hostIds[0]);
                }

                var hostVersionParams =
                    [{  hostId: hostIds[0],
                        dateRange: leftDate,
                        moduleName: moduleName
                     },
                     {  hostId: hostIds[1],
                         dateRange: rightDate,
                         moduleName: moduleName
                     }
                    ];

                return _(factScanDataService.getVersion(hostVersionParams[1]))
                        .then(function(result) {
                            return resolveEmptyVersions(result);
                        }).thenAll(function(firstResult) {

                            return factScanDataService.getVersion(hostVersionParams[0])
                                    .then(function(secondResult) {
                                        if (_.isEmpty(secondResult.versions)) {
                                            secondResult = resolveEmptyVersions(secondResult);
                                        }

                                        return [firstResult, secondResult];
                                    });
                        }).thenAll(function(results) {
                            var finalSet;

                            if (singleHostMode) {
                                finalSet = dedupeVersions(results.reverse());
                            } else {
                                finalSet = _.pluck(results, 'versions[0]').reverse();
                            }

                            return finalSet;
                        }).thenMap(function(versionData) {
                            if (versionData) {
                                return factScanDataService.getFacts(versionData);
                            } else {
                                return { fact: [] };
                            }
                        }).thenAll(function(hostFacts) {
                            return hostFacts;
                        });
            };
        }
    ];
