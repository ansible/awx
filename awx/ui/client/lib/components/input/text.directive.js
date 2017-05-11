function link (scope, el, attrs, form) {
    scope.config.state = scope.config.state || {};
    let state = scope.config.state;
    let input = el.find('input')[0];

    setDefaults();

    scope.form = form.use('input', state, input);

    function setDefaults () {
        if (scope.tab === '1') {
            input.focus();
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
            col: '@',
            tab: '@'
        }
    };
}

atInputText.$inject = ['PathService'];

export default atInputText;
