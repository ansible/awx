function link (scope, el, attrs, form) {
    form.use('input', scope, el);
}

function atInputText (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: pathService.getPartialPath('components/input/text'),
        link,
        scope: {
            config: '=',
            col: '@'
        }
    };
}

atInputText.$inject = ['PathService'];

export default atInputText;
