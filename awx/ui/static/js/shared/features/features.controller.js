export default ['$rootScope', function ($rootScope) {

    this.isFeatureEnabled = function(feature){
        if(_.isEmpty($rootScope.features)){
            return false;
        } else{
            return $rootScope.features[feature] || false;
        }
    };
}];
