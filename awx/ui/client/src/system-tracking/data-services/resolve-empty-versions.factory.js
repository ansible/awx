import moment from '../../shared/moment/moment';

function resolveEmptyVersions(service, _, candidate, previousResult) {

    candidate = _.merge({}, candidate);

    // theoretically, returning no versions, but also returning only a single version for _a particular date_ acts as an empty version problem.  If there is only one version returned, you'll need to check previous dates as well.
    if (_.isEmpty(candidate.versions) || candidate.versions.length === 1) {
        // this marks the end of the date put in the datepicker.  this needs to be the end, rather than the beginning of the date, because you may have returned one valid version on the date the datepicker had in it.
        var originalStartDate = candidate.dateRange.to.clone();

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
