/* jshint unused: vars */

export default function() {
    return {
        templateUrl: '/static/js/main-menu/menu-toggle.partial.html',
        restrict: 'E',
        require: '^^mainMenu',
        scope: {
            width: '@',
            height: '@',
            barHeight: '@'
        },
        link: function(scope, element, attrs, mainMenuController) {
            scope.$on('$destroy', function() {
                element.off('click');
            });

            element.on("click", function(e) {
                e.preventDefault();
                e.stopPropagation();
                scope.$apply(function() {
                    mainMenuController.toggle();
                });
            });
        }
    };
}
