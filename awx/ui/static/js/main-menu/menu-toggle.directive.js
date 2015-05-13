/* jshint unused: vars */

export default function() {
    return {
        templateUrl: '/static/js/main-menu/menu-toggle.partial.html',
        restrict: 'E',
        scope: {
            width: '@',
            height: '@',
            barHeight: '@'
        },
        link: function(scope, element, attrs) {
            element.on("click", function(e) {
                e.preventDefault();
                e.stopPropagation();
                $(".Menu--main").toggleClass("Menu--open");
                element.toggleClass("MenuToggle--open");
            });
        }
    };
}
