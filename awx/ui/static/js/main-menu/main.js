import mainMenu from './main-menu.directive';
import menuItem from './menu-item.directive';

export default
    angular.module('mainMenu', [])
        .directive('menuItem', menuItem)
        .directive('mainMenu', mainMenu);
