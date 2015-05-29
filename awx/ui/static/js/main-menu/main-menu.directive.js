/* jshint unused: vars */

export default function() {
    return {
        restrict: 'E',
        controllerAs: 'mainMenu',
        templateUrl: '/static/js/main-menu/main-menu.partial.html',
        controller: ['$scope', function($scope) {
            this.open = function() {
                $scope.isOpen = true;
            };

            this.close = function() {
                $scope.isOpen = false;
            };

            this.toggle = function() {
                $scope.isOpen = !$scope.isOpen;
            };

            $scope.isOpen = false;
        }],
        scope: {
            menuStyle: '&menuStyle',
            currentUser: '='
        },
        link: function(scope, element, attrs) {
            scope.menuStyleClassName = 'blah';
            scope.$watch(function() {
                return scope.$eval(scope.menuStyle);
            }, function(newValue) {
                scope.menuStyleClassName = 'MainMenu--' + newValue;
            });
            scope.$watch('isOpen', function(isOpen) {
                if (isOpen) {
                    element.find('.MainMenu').addClass("Menu--open");
                    element.find('menu-toggle-button').addClass("MenuToggle--open");
                } else {
                    element.find('.MainMenu').removeClass("Menu--open");
                    element.find('menu-toggle-button').removeClass("MenuToggle--open");
                }
            });
        }
    };
}
