function atActionGroup (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/action/action-group'),
        scope: {
            col: '@',
            pos: '@'
        }
    };
}

atActionGroup.$inject = ['PathService'];

export default atActionGroup;
