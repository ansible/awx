function atPanelHeading () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/panel-heading.partial.html',
        scope: {
            config: '='
        }
    };
}

export default atPanelHeading;
