import mainMenu from './main-menu.directive';
import menuItem from './menu-item.directive';
import menuToggle from './menu-toggle.directive';
import portalModeLink from './portal-mode-link.directive';
import webSocketStatus from './web-socket-status.directive';

import includePartial from 'tower/shared/include-partial/main';
import shared from 'tower/shared/main';

export default
    angular.module('mainMenu',
                   [    includePartial.name,
                        shared.name
                   ])
        .directive('portalModeLink', portalModeLink)
        .directive('menuItem', menuItem)
        .directive('menuToggleButton', menuToggle)
        .directive('webSocketStatus', webSocketStatus)
        .directive('mainMenu', mainMenu);
