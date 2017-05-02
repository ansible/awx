function atToggleContent () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/component/toggle/content.partial.html',
        scope: {
          config: '='
        }
    };
}

export default atToggleContent;
