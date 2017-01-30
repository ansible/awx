import route from './setup.route';
import icon from '../shared/icon/main';

export default
    angular.module('setupMenu',
        [ icon.name])
        .run(['$stateExtender', 'I18NInit',
             function($stateExtender, I18NInit) {
            I18NInit();

            $stateExtender.addState(route);
        }]);
