export default ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', '$http', '$q',
function ($rootScope, Rest, GetBasePath, ProcessErrors, $http, $q) {
    return {
            getFeatures: function(){
                var promise;
                Rest.setUrl(GetBasePath('config'));
                promise = Rest.get();
                return promise.then(function (data) {
                    $rootScope.features = data.data.license_info.features;
                    return $rootScope.features;
                }).catch(function (response) {
                    ProcessErrors($rootScope, response.data, response.status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to get license info. GET returned status: ' +
                        response.status
                    });
                });

            },
            get: function(){
                if(_.isEmpty($rootScope.features)){
                    return this.getFeatures();
                } else {
                    // $q.when will ensure that the result is returned
                    // as a resovled promise.
                    return $q.when($rootScope.features);
                }
            }
        };
}];
