import route from './adhoc.route';
import adhocController from './adhoc.controller';
import form from './adhoc.form';

export default angular.module('adhoc', [])
    .controller('adhocController', adhocController)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(route);
    }])
    .factory('adhocForm', form);
