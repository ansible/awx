function atToggleButton () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/toggle/button.partial.html',
        scope: {
          config: '='
        }
    };
}

export default atToggleButton;
