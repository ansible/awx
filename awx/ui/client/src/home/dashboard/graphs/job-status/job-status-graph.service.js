/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ["Rest", "GetBasePath", "ProcessErrors", "$q", JobStatusGraphData];

function JobStatusGraphData(Rest, getBasePath, processErrors, $q) {
    return {
        get: function(period, jobType, status) {
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
    };
}
