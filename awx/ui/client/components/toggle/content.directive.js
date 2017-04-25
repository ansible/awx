function atToggleContent () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/toggle/content.partial.html',
        scope: {
          config: '='
        }
    };
}

export default atToggleContent;
