/* jshint unused: vars */

export default function() {
    return {
        restrict: 'E',
        templateUrl: '/static/js/main-menu/main-menu.partial.html',
        scope: {
            menuStyle: '&menuStyle',
            currentUser: '='
        }
    };
}
