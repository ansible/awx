let $state;

function link (scope, el, attrs, form) {
    scope.config.state = scope.config.state || {};
    let state = scope.config.state;

    scope.form = form.use('action', state);

    switch(scope.config.type) {
        case 'cancel':
            setCancelDefaults(scope);
            break;
        case 'save':
            setSaveDefaults(scope);
            break;
        default:
            break;
    }

    function setCancelDefaults (scope) {
        scope.text = 'CANCEL';
        scope.fill = 'Hollow';
        scope.color = 'white';
        scope.action = () => $state.go('^');
    }

    function setSaveDefaults (scope) {
        scope.text = 'SAVE';
        scope.fill = '';
        scope.color = 'green';
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
