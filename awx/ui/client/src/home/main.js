import dashboard from './dashboard/main';
import HomeController from './home.controller';
import route from './home.route';

export default
    angular.module('home', [
        dashboard.name
    ])
    .controller('HomeController', HomeController)
    .run(['$stateExtender', function($stateExtender){
        $stateExtender.addState(route);
    }]);
