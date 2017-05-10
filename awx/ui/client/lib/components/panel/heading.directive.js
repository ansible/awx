function link (scope, el, attrs, panel) {
    panel.use(scope);
}

function atPanelHeading (pathService) {
    return {
        restrict: 'E',
        require: '^^atPanel',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/heading'),
        link,
        scope: {
            config: '='
        }
    };
}

atPanelHeading.$inject = ['PathService'];

export default atPanelHeading;
