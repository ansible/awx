/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', 'ConfigService',
function ($rootScope, ConfigService) {
    return {
            get: function(){
                if (_.isEmpty($rootScope.features)) {
                    var config = ConfigService.get();
                    if(config){
                        $rootScope.features = config.license_info.features;
                        if($rootScope.featuresConfigured){
                            $rootScope.featuresConfigured.resolve($rootScope.features);
                        }
                        return $rootScope.features;
                    }
                }
                else{
                    return $rootScope.features;
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
