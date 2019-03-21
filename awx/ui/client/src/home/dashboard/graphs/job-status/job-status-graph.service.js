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
    "$timeout",
    JobStatusGraphData];

function JobStatusGraphData(Rest, getBasePath, processErrors, $rootScope, $q, $timeout) {

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
        Rest.setHeader({'X-WS-Session-Quiet': true});
        Rest.setUrl(url);
        return Rest.get()
            .then(function(value) {
                if(status === "successful" || status === "failed"){
                    delete value.data.jobs[status];
                }
                return value.data;
            })
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
    }

    return {
        pendingRefresh: false,
        refreshTimerRunning: false,
        refreshTimer: angular.noop,
        destroyWatcher: angular.noop,
        setupWatcher: function(period, jobType) {
            const that = this;
            that.destroyWatcher =
                $rootScope.$on('ws-jobs', function() {
                    if (!that.refreshTimerRunning) {
                        that.timebandGetData(period, jobType);
                    } else {
                        that.pendingRefresh = true;
                    }
            });
        },
        timebandGetData: function(period, jobType) {
            getData(period, jobType).then(function(result) {
                $rootScope.
                    $broadcast('DataReceived:JobStatusGraph',
                               result);
                return result;
            });
            this.pendingRefresh = false;
            this.refreshTimerRunning = true;
            this.refreshTimer = $timeout(() => {
                if (this.pendingRefresh) {
                    this.timebandGetData(period, jobType);
                } else {
                    this.refreshTimerRunning = false;
                }
            }, 5000);
        },
        get: function(period, jobType, status) {

            this.destroyWatcher();
            $timeout.cancel(this.refreshTimer);
            this.refreshTimerRunning = false;
            this.pendingRefresh = false;
            this.setupWatcher(period, jobType);

            return getData(period, jobType, status);

        }
    };
}
