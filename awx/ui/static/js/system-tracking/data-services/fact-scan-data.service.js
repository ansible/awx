/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'GetBasePath', 'ProcessErrors', 'lodashAsPromised',
function (Rest, GetBasePath, ProcessErrors, _) {

    function buildUrl (host_id, module, startDate, endDate) {
        var url = GetBasePath('hosts') + host_id + '/fact_versions/',
            params= [["module", module] , ['from', startDate.format()],  ['to', endDate.format()]];

        params = params.filter(function(p){
            return !_.isEmpty(p[1]);
        });
        params = params.map(function(p){
            return p.join("=");
        }).join("&");
        url = _.compact([url, params]).join("?");
        return url;
    }

    return {
        getHostFacts: function(host, moduleName, date, fetchScanNumber) {

            var getVersion = _.partial(this.getVersion, host, moduleName);
            var getFacts = this.getFacts;

            return getVersion(date.from, date.to, fetchScanNumber)
                    .then(function(versionData) {
                        if (_.isEmpty(versionData)) {
                            var retryStartDate = date.from.clone().subtract(1, 'year');
                            return getVersion(retryStartDate, date.from, fetchScanNumber);
                        } else {
                            return versionData;
                        }
                    })
                    .then(function(versionData) {
                        if (_.isEmpty(versionData)) {
                            return { fact: [] };
                        } else {
                            return getFacts(versionData);
                        }
                    });

        },
        getFacts: function(version) {
            var promise;
            Rest.setUrl(version.related.fact_view);
            promise = Rest.get();
            return promise.then(function (response) {
                return response.data;
            }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get license info. GET returned status: ' +
                    response.status
                });
            });
        },

        getVersion: function(versionParams){
            //move the build url into getVersion and have the
            // parameters passed into this
            var promise;
            var hostId = versionParams.hostId;
            var startDate = versionParams.dateRange.from;
            var endDate = versionParams.dateRange.to;
            var module = versionParams.moduleName;

            var url = buildUrl(hostId, module, startDate, endDate);

            Rest.setUrl(url);
            promise = Rest.get();
            return promise.then(function(response) {
                return response.data.results;
            }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get license info. GET returned status: ' +
                    response.status
                });
            });
        }
    };
}];
