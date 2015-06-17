import moment from 'tower/shared/moment/moment';

function resolveEmptyVersions(service, _, candidate, previousResult) {

    candidate = _.merge({}, candidate);

    if (_.isEmpty(candidate.versions)) {
        var originalStartDate = candidate.dateRange.from.clone();

        if (!_.isUndefined(previousResult)) {
            candidate.dateRange.from = moment(previousResult.versions[0].timestamp);
        } else {
            candidate.dateRange.from = originalStartDate.clone().subtract(1, 'year');
        }

        candidate.dateRange.to = originalStartDate;

        return service.getVersion(candidate);
    }

    return _.promise(candidate);

}

export default
    [   'factScanDataService',
        'lodashAsPromised',
        function(factScanDataService, lodash) {
            return _.partial(resolveEmptyVersions, factScanDataService, lodash);
        }
    ];
