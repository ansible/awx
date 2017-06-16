function atPanelBody (pathService) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: pathService.getPartialPath('components/utility/divider'),
        scope: false
    };
}

atPanelBody.$inject = ['PathService'];

export default atPanelBody;
