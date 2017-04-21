function atBadge () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/badge.partial.html',
        scope: {
            config: '='
        }
    };
}

export default atBadge;
