function atInputLabel (pathService) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: pathService.getPartialPath('components/input/label')
    };
}

atInputLabel.$inject = ['PathService'];

export default atInputLabel;
