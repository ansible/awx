import route from './setup.route';
import icon from '../shared/icon/main';

export default
    angular.module('setupMenu',
                   [    'AboutAnsibleHelpModal',
                        'ConfigureTowerHelper',
                        icon.name
                   ])
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);
