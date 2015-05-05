export default ['$rootScope', function ($rootScope) {

    this.isFeatureEnabled = function(feature){
        return $rootScope.features[feature] || false;
    };
}];
