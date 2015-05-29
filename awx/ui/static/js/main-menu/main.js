import mainMenu from './main-menu.directive';
import menuItem from './menu-item.directive';
import menuToggle from './menu-toggle.directive';
import webSocketStatus from './web-socket-status.directive';
import defaultMenu from './default-menu.directive';
import portalMenu from './portal-menu.directive';

import shared from 'tower/shared/main';

export default
    angular.module('mainMenu',
                   [    shared.name
                   ])
        .directive('menuItem', menuItem)
        .directive('defaultMenu', defaultMenu)
        .directive('portalMenu', portalMenu)
        .directive('menuToggleButton', menuToggle)
        .directive('webSocketStatus', webSocketStatus)
        .directive('mainMenu', mainMenu);
