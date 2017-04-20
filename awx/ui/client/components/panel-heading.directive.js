function atPanelHeading () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl: 'static/partials/components/panel-heading.partial.html',
        scope: {
            heading: '=config'
        }
    };
}

export default atPanelHeading;
