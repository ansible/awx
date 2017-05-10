let $state;

function applyCancelProperties (scope) {
    scope.text = scope.config.text || 'CANCEL';
    scope.fill = 'Hollow';
    scope.color = 'white';
    scope.disabled = false;
    scope.action = () => $state.go('^');
}

function applySaveProperties (scope) {
    scope.text = 'SAVE';
    scope.fill = '';
    scope.color = 'green';
    scope.disabled = true;
}

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

function atFormAction (_$state_, pathService) {
    $state = _$state_;

    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: pathService.getPartialPath('components/action/action'),
        link,
        scope: {
            config: '='
        }
    };
}

atFormAction.$inject = ['$state', 'PathService'];

export default atFormAction;
