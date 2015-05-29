export default function() {
    return {
        restrict: 'E',
        templateUrl: '/static/js/main-menu/menu-portal.partial.html',
        link: function(scope, element) {
            var contents = element.contents();
            contents.unwrap();

            scope.$on('$destroy', function() {
                contents.remove();
            });
        }
    };
}

