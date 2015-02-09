export default
    [   "Rest",
        "GetBasePath",
        "ProcessErrors",
        "$q",
        HostCountGraphData
    ];

function HostCountGraphData(Rest, getBasePath, processErrors, $q) {

    function pluck(property, promise) {
        return promise.then(function(value) {
            return value[property];
        });
    }

    function getLicenseData() {
        var url = getBasePath('config');
        Rest.setUrl(url);
        return Rest.get()
        .then(function (data){
            var license = data.data.license_info.instance_count;
            return license;
        });
    }

    function getHostData() {
        var url = getBasePath('dashboard')+'graphs/inventory/';
        Rest.setUrl(url);
        return pluck('data', Rest.get());
    }

    return {
        get: function() {
            return $q.all({
                license: getLicenseData(),
                hosts: getHostData()
            }).catch(function (response) {
                var errorMessage = 'Failed to get: ' + response.url + ' GET returned: ' + response.status;
                processErrors(null, response.data, response.status, null, { hdr: 'Error!',
                              msg: errorMessage
                });
                return $q.reject(response);
            });
        }
    };
}
