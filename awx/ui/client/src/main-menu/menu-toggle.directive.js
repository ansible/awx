/* jshint unused: vars */

export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                templateUrl: templateUrl('main-menu/menu-toggle'),
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
    ];
