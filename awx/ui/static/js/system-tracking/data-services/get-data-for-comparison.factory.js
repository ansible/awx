export default
    [   'factScanDataService',
        'lodashAsPromised',
        function(factScanDataService, _) {
            return function(hostIds, moduleName, leftDate, rightDate) {

                if (hostIds.length === 1) {
                    hostIds = hostIds.concat(hostIds[0]);
                }

                return _(hostIds)
                    .promise()
                    .thenMap(function(hostId, index) {
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
                    });
            };
        }
    ];
