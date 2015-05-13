export default ['$location', function($location) {
    return {
        link: function(scope, element, attrs) {
            var itemPath = attrs.href.replace(/^#/, '');

            scope.$watch(function() {
                return $location.path();
            }, function(currentPath) {
                if (currentPath === itemPath) {
                    element.addClass('MenuItem--active');
                } else {
                    element.removeClass('MenuItem--active');
                }
            });
        }
    };
}];
