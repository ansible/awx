export default
    [   '$rootScope',
        '$routeParams',
        function($rootScope, $routeParams) {
            $rootScope.$on('$routeChangeSuccess', function(e, newRoute) {
                if (angular.isUndefined(newRoute.model)) {
                    var keys = Object.keys(newRoute.params);
                    var models = keys.reduce(function(model, key) {
                        model[key] = newRoute.locals[key];
                        return model;
                    }, {});

                    $routeParams.model = models;
                }
            });
        }
    ];
