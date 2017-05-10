function atActionGroup (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        templateUrl: pathService.getPartialPath('components/action/action-group'),
        scope: {
            col: '@',
            pos: '@'
        }
    };
}

atActionGroup.$inject = ['PathService'];

export default atActionGroup;
