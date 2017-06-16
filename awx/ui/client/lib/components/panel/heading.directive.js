function link (scope, el, attrs, panel) {
    panel.use(scope);
}

function atPanelHeading (pathService) {
    return {
        restrict: 'E',
        require: '^^atPanel',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/heading'),
        link
    };
}

atPanelHeading.$inject = ['PathService'];

export default atPanelHeading;
