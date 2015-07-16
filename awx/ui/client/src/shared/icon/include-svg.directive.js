export default ['$http', '$rootScope', function($http, $rootScope) {
    return {
        restrict: 'E',
        link: function(scope, element, attrs) {
            var path = attrs.href;

            $http.get(path).then(function(response) {
                element.append(response.data);
                $rootScope.$emit('include-svg.svg-ready');
            });
        }
    };
}];
