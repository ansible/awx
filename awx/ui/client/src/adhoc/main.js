import route from './adhoc.route';
import adhocController from './adhoc.controller';
import form from './adhoc.form';

export default angular.module('adhoc', ["ngRoute"])
    .controller('adhocController', adhocController)
    .config(['$routeProvider', function($routeProvider) {
        var url = route.route;
        delete route.route;
        $routeProvider.when(url, route);
    }])
    .factory('adhocForm', form);
