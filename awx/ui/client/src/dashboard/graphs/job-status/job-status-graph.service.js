/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
["Rest",
    "GetBasePath",
    "ProcessErrors",
    "$rootScope",
    "$q",
    JobStatusGraphData];

function JobStatusGraphData(Rest, getBasePath, processErrors, $rootScope, $q) {

    function pluck(property, promise, status) {
        return promise.then(function(value) {
            if(status === "successful" || status === "failed"){
                delete value[property].jobs[status];
            }
            return value[property];
        });
    }

    function getData(period, jobType, status) {
        var url, dash_path = getBasePath('dashboard');
        if(dash_path === '' ){
            processErrors(null,
                          null,
                          null,
                          null, {
                hdr: 'Error!',
                msg: "There was an error. Please try again."
            });
            return;
        }
        url = dash_path + 'graphs/jobs/?period='+period+'&job_type='+jobType;
        Rest.setUrl(url);
        var result = Rest.get()
        .catch(function(response) {
            var errorMessage = 'Failed to get: ' + response.url + ' GET returned: ' + response.status;

            processErrors(null,
                          response.data,
                          response.status,
                          null, {
                hdr: 'Error!',
                msg: errorMessage
            });
            return $q.reject(response);
        });

        return pluck('data', result, status);
    }

    return {
        destroyWatcher: angular.noop,
        setupWatcher: function(period, jobType) {
            this.destroyWatcher =
                $rootScope.$on('ws-jobs', function() {
                    getData(period, jobType).then(function(result) {
                        $rootScope.
                            $broadcast('DataReceived:JobStatusGraph',
                                       result);
                        return result;
                    });
            });
        },
        get: function(period, jobType, status) {

            this.destroyWatcher();
            this.setupWatcher(period, jobType);

            return getData(period, jobType, status);

        }
    };
}
