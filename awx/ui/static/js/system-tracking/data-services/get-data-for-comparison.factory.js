/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'factScanDataService',
        'getModuleOptions',
        'lodashAsPromised',
        function(factScanDataService, getModuleOptions, _) {
            return function(hostIds, moduleName, leftDate, rightDate) {

                var moduleOptions;

                if (hostIds.length === 1) {
                    hostIds = hostIds.concat(hostIds[0]);
                }

                return getModuleOptions(hostIds[0])
                    .then(function(modules) {
                        moduleOptions = modules;
                        return modules;
                    }).then(function() {
                        return hostIds;
                    }).thenMap(function(hostId, index) {
                        var date = leftDate;
                        var fetchScanNumber;

                        if (index === 1) {
                            date = rightDate;
                        } else {
                            if (rightDate.from.isSame(leftDate.from, 'day')) {
                                fetchScanNumber = 1;
                            }
                        }

                        var params =
                            [   hostId,
                                moduleName,
                                date,
                                fetchScanNumber
                            ];

                        return params;
                    }).thenMap(function(params) {
                        var getHostFacts =
                            _.spread(factScanDataService.getHostFacts)
                                .bind(factScanDataService);

                        return getHostFacts(params);
                    }).then(function(hostFacts) {
                        hostFacts.moduleOptions = moduleOptions;
                        return hostFacts;
                    });
            };
        }
    ];
