/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'factScanDataService',
        'getModuleOptions',
        'resolveVersions',
        'lodashAsPromised',
        function(factScanDataService, getModuleOptions, resolveVersions, _) {
            return function(hostIds, moduleName, leftDate, rightDate) {

                if (hostIds.length === 1) {
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

                return _(hostVersionParams)
                        .map(function(versionParam) {
                            var versionWithRequest =
                                [   versionParam,
                                    factScanDataService.
                                     getVersion(versionParam)
                                ];

                            return versionWithRequest;
                        }).thenAll(function(versions) {
                            return resolveVersions(versions);
                        }, true)
                        .thenMap(function(versionData) {
                            if (versionData) {
                                return factScanDataService.getFacts(versionData);
                            } else {
                                return { fact: [] };
                            }
                        })
                        .thenAll(function(hostFacts) {
                            return hostFacts;
                        });
            };
        }
    ];
