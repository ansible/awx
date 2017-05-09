function link (scope, el, attrs, form) {
    form.use('action', scope, el);

    switch(scope.config.type) {
        case 'cancel':
            applyCancelProperties(scope);
            break;
        case 'save':
            applySaveProperties(scope);
            break;
    }
}

function applyCancelProperties (scope) {
    scope.text = 'CANCEL';
    scope.fill = 'Hollow';
    scope.color = 'white';
    scope.disabled = false;
}

function applySaveProperties (scope) {
    scope.text = 'SAVE';
    scope.fill = '';
    scope.color = 'green';
    scope.disabled = true;
}

function atFormAction (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: pathService.getPartialPath('components/form/form-action'),
        link,
        scope: {
            config: '='
        }
    };
}

atFormAction.$inject = ['PathService'];

export default atFormAction;
