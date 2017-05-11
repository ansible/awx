let eventService;
let pathService;

function link (scope, el, attrs, form) {
    scope.config.state = scope.config.state || {};

    let input = el.find('input')[0];
    let select = el.find('select')[0];
    let state = scope.config.state;

    setDefaults();

    scope.form = form.use('input', state);

    let listeners = eventService.addListeners(scope, [
        [input, 'focus', () => select.focus],
        [select, 'mousedown', () => scope.$apply(scope.open = !scope.open)],
        [select, 'focus', () => input.classList.add('at-Input--focus')],
        [select, 'change', () => {
            scope.open = false;
            check();
        }],
        [select, 'blur', () => {
            input.classList.remove('at-Input--focus');
            scope.open = scope.open && false;
        }]
    ]);

    scope.$on('$destroy', () => eventService.remove(listeners));

    function setDefaults () {
        if (scope.tab === 1) {
            select.focus();
        }

        state.isValid = state.isValid || false;
        state.validate = state.validate ? validate.bind(null, state.validate) : validate;
        state.check = state.check || check;
        state.message = state.message || '';
        state.required = state.required || false;
    }

    function validate (fn) {
        let isValid = true;

        if (state.required && !state.value) {
            isValid = false;    
        } else if (fn && !fn(scope.config.input)) {
            isValid = false;  
        }

        return isValid;
    }

    function check () {
        let isValid = state.validate();

        if (isValid !== state.isValid) {
            state.isValid = isValid;
            form.check();
        }
    }
}

function atInputSelect (_eventService_, _pathService_) {
    eventService = _eventService_;
    pathService = _pathService_;

    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: pathService.getPartialPath('components/input/select'),
        link,
        scope: {
            config: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputSelect.$inject = [
    'EventService',
    'PathService'
];

export default atInputSelect;
