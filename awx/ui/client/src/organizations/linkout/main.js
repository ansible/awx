import routes from './organizations-linkout.route';

export default angular.module('organizationsLinkout', [])
    .run(['$stateExtender', function($stateExtender) {
        routes.forEach(function(route) {
            $stateExtender.addState(route);
        });
    }]);
