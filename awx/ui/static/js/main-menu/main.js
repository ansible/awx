import mainMenu from './main-menu.directive';
import menuItem from './menu-item.directive';
import portalModeLink from './portal-mode-link.directive';

export default
    angular.module('mainMenu', [])
        .directive('portalModeLink', portalModeLink)
        .directive('menuItem', menuItem)
        .directive('mainMenu', mainMenu);
