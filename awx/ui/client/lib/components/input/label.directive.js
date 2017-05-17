function atInputLabel (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        templateUrl: pathService.getPartialPath('components/input/label'),
        scope: {
            state: '='
        }
    };
}

atInputLabel.$inject = ['PathService'];

export default atInputLabel;
