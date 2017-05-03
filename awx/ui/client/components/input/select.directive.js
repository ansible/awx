// TODO: i18n

function atInputSelect () {
    function link (scope, element, attrs) {
    }

    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/input/select.partial.html',
        link,
        scope: {
            config: '='
        }
    };
}

export default atInputSelect;
