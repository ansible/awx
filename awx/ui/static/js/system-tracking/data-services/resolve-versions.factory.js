function resolveVersions(service, _, results) {

    function transformToObjects(versionArray) {

        var converted = versionArray[0];
        converted.versions = versionArray[1];

        return converted;

    }

    function resolveEmpties(result) {
        if (_.isEmpty(result.versions)) {
            var originalStartDate = result.dateRange.from;
            result.dateRange.from = originalStartDate.clone().subtract(1, 'year');
            result.dateRange.to = originalStartDate;
            return [result, service.getVersion(result)];
        }

        return [result, _.promise(result.versions)];
    }

    function resolveDuplicates(nonEmptyResults) {
        var allSameHost =
            _.every(nonEmptyResults, { 'hostId': nonEmptyResults[0].hostId });

        if (allSameHost) {
            var firstTimestamp = nonEmptyResults[0].versions[0].timestamp;

            var hostIdsWithDupes =
                _(nonEmptyResults)
                    .pluck('versions[0]')
                    .filter('timestamp', firstTimestamp)
                    .map(function(version, index) {
                        return nonEmptyResults[index].hostId;
                    })
                    .value();

            if (hostIdsWithDupes.length === 1) {
                return _.pluck(nonEmptyResults, 'versions[0]');
            }

            return nonEmptyResults.map(function(scan, index) {
                var hasDupe =
                    _.include(hostIdsWithDupes, scan.hostId);

                if (hasDupe && index === 1) {
                    return scan.versions[1];
                } else {
                    return scan.versions[0];
                }
            });

        } else {
            return _.pluck(nonEmptyResults, 'versions[0]');
        }
    }

    return _(results)
            .map(transformToObjects)
            .map(resolveEmpties)
            .thenAll(function(resolved) {
                var versionObjects = resolved.map(transformToObjects);
                return resolveDuplicates(versionObjects);
            }, true)
            .value();
}

export default
    [   'factScanDataService',
        'lodashAsPromised',
        function(factScanDataService, lodash) {
            return _.partial(resolveVersions, factScanDataService, lodash);
        }
    ];
