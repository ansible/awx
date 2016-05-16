/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', '$http',
    '$q', 'ConfigService',
function ($rootScope, Rest, GetBasePath, ProcessErrors, $http, $q,
    ConfigService) {
    var license_info;

    return {
            getFeatures: function(){
                var config = ConfigService.get();
                license_info = config.license_info;
                $rootScope.features = config.license_info.features;
                return $rootScope.features;
                // var promise;
                // Rest.setUrl(GetBasePath('config'));
                // promise = Rest.get();
                // return promise.then(function (data) {
                //     license_info = data.data.license_info;
                //     $rootScope.features = data.data.license_info.features;
                //     return $rootScope.features;
                // }).catch(function (response) {
                //     ProcessErrors($rootScope, response.data, response.status, null, {
                //         hdr: 'Error!',
                //         msg: 'Failed to get license info. GET returned status: ' +
                //         response.status
                //     });
                // });
            },
            get: function(){
                if(_.isEmpty($rootScope.features)){
                    return this.getFeatures();
                } else {
                    // $q.when will ensure that the result is returned
                    // as a resovled promise.
                    return $q.when($rootScope.features);
                }
            },
            featureEnabled: function(feature) {
                if($rootScope.features && $rootScope.features[feature] && $rootScope.features[feature] === true) {
                    return true;
                }
                else {
                    return false;
                }
            }
        };
}];
