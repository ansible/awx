export default ['$rootScope', function ($rootScope) {

    this.isFeatureEnabled = function(feature){
        if($rootScope.features[feature] === false){
            return false;
        } else {
            return true;
        }
    };
}];
