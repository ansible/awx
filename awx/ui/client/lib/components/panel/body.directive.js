function atPanelBody (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/body')
    };
}

atPanelBody.$inject = ['PathService'];

export default atPanelBody;
