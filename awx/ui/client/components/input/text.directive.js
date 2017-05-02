// TODO: i18n

function atInputText () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/input/text.partial.html',
        scope: {
            config: '='
        }
    };
}

export default atInputText;
