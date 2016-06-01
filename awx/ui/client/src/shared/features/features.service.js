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
                if(config){
                    license_info = config.license_info;
                    $rootScope.features = config.license_info.features;
                    $rootScope.$emit('featuresLoaded');
                    return $rootScope.features;
                }
                else {
                    return {};
                }
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
