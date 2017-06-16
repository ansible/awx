function atPanelBody (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/body'),
        scope: {
            state: '='
        }
    };
}

atPanelBody.$inject = ['PathService'];

export default atPanelBody;
