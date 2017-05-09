function atFormActionGroup (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: pathService.getPartialPath('components/form/form-action-group'),
        scope: {
            config: '='
        }
    };
}

atFormActionGroup.$inject = ['PathService'];

export default atFormActionGroup;
