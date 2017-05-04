function atPanelBody (pathService) {
    return {
        restrict: 'E',
        require: '^^atPanel',
        transclude: true,
        templateUrl: pathService.getPartialPath('components/panel/body'),
    };
}

atPanelBody.$inject = ['PathService'];

export default atPanelBody;
