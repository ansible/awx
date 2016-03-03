import route from './setup.route';
import icon from '../shared/icon/main';

export default
    angular.module('setupMenu',
        [ icon.name])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
