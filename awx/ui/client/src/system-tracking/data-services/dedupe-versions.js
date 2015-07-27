export default
    function dedupeVersions(nonEmptyResults) {

        if (_.any(nonEmptyResults, 'versions.length', 0)) {
            return _.pluck(nonEmptyResults, 'versions[0]');
        }

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

        var bestScanResults = _.max(nonEmptyResults, "versions.length");

        return nonEmptyResults.map(function(scan, index) {
            var hasDupe =
                _.include(hostIdsWithDupes, scan.hostId);

            if (hasDupe && index === 1) {
                return bestScanResults.versions[0];
            } else {
                return bestScanResults.versions[1];
            }
        });

    }
