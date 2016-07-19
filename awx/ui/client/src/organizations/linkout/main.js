import routes from './organizations-linkout.route';
import AddUsers from './addUsers/main';

export default angular.module('organizationsLinkout', [AddUsers.name])
    .run(['$stateExtender', function($stateExtender) {
        routes.forEach(function(route) {
            $stateExtender.addState(route);
        });
    }]);
