// TODO: i18n

function atInputSearch () {
    function link (scope) {
        scope.config = scope.config || {};
        scope.config.placeholder = scope.config.placeholder || 'SEARCH';
    }

    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/input/search.partial.html',
        link,
        scope: {
            config: '='
        }
    };
}

export default atInputSearch;
