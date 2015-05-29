export default ['$http', function($http) {
    return {
        restrict: 'E',
        link: function(scope, element, attrs) {
            var path = attrs.href;

            $http.get(path).then(function(response) {
                element.append(response.data);
            });
        }
    };
}];
