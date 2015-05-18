export default ['Rest', 'GetBasePath', 'ProcessErrors', 'lodashAsPromised',
function (Rest, GetBasePath, ProcessErrors, _) {
    return {
        getHostFacts: function(host, moduleName, date, fetchScanNumber) {

            var version =this.getVersion(host, moduleName, date.from, date.to, fetchScanNumber);
            var getFacts = this.getFacts;

            return version
                    .then(function(versionData) {
                        if (_.isEmpty(versionData)) {
                            return [];
                        } else {
                            return getFacts(versionData);
                        }
                    });

        },
        getFacts: function(version) {
            var promise;
            Rest.setUrl(version.related.fact_view);
            promise = Rest.get();
            return promise.then(function (data) {
                return data.data.fact;
            }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get license info. GET returned status: ' +
                    response.status
                });
            });
        },

        getVersion: function(host_id, module, startDate, endDate, fetchScanNumber){
            //move the build url into getVersion and have the
            // parameters passed into this
            var promise,
                url = this.buildUrl(host_id, module, startDate, endDate);

            fetchScanNumber = fetchScanNumber || 0;

            Rest.setUrl(url);
            promise = Rest.get();
            return promise.then(function(data) {
                return data.data.results[fetchScanNumber];
            }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get license info. GET returned status: ' +
                    response.status
                });
            });
        },

        buildUrl: function(host_id, module, startDate, endDate){
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
    };
}];
