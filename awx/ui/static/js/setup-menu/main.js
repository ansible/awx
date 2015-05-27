import route from './setup.route';

export default
    angular.module('setupMenu',
                   [    'AboutAnsibleHelpModal',
                        'LicenseHelper',
                        'ConfigureTowerHelper',
                        'CreateCustomInventoryHelper'
                   ])
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route)
        }]);

