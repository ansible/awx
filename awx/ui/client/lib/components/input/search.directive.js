// TODO: i18n

function atInputSearch (pathService) {
    function link (scope) {
        scope.config = scope.config || {};
        scope.config.placeholder = scope.config.placeholder || 'SEARCH';
    }

    return {
        restrict: 'E',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/input/search'),
        link,
        scope: {
            config: '='
        }
    };
}

atInputSearch.$inject = ['PathService'];

export default atInputSearch;
